"""
Copyright 2021 Venceslas Roullier, Daniel Santos Bustos, Guillem Sanyas, Julien Tagnani, Agustin Zorzano

This file is part of OpenEmailAntispam.

    OpenEmailAntispam is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenEmailAntispam is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenEmailAntispam.  If not, see https://www.gnu.org/licenses/.
"""

import re
import os
import datetime
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from spam import db
from spam.models import (
    WhiteList,
    BlackList,
    WhiteListRegularExpression,
    BlackListRegularExpression,
    Quarantine,
    History,
)
from spam.message_creator import MessageCreator
from dotenv import load_dotenv

load_dotenv()

BASE_PATH = os.environ.get("BASE_PATH")
TEMPLATE_NAME = "captcha_email.html"
APP_EMAIL = os.environ.get("EMAIL_USER")


def fulfils_expression(mail, email_subject, expressions):
    """It returns True if one of the regular expressions in the expressions list matches the email address
    or the email subject"""
    for expression in expressions:
        check_sentence = mail
        if expression.expression_type == "email_subject":
            check_sentence = email_subject
        if re.fullmatch(expression.expression, check_sentence):
            return True
    return False


def create_header(sender, receiver):
    ENCRYPTOR_PRIVATE_KEY_PATH = os.environ.get("ENCRYPTOR_PRIVATE_KEY_PATH")
    with open(ENCRYPTOR_PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None, backend=default_backend())
        data = {
            "sender": sender,
            "receiver": receiver,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=5)
        }
        encoded = jwt.encode(data, private_key, algorithm="RS256")
        return encoded


def check_validation_header(message, receiver, sender):
    ENCRYPTOR_PUBLIC_KEY_PATH = os.environ.get("ENCRYPTOR_PUBLIC_KEY_PATH")
    with open(ENCRYPTOR_PUBLIC_KEY_PATH, "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read(), backend=default_backend())
        try:
            validation_header = message.get_validation_header()
            if not validation_header:
                # The email was not a reply from our service
                return False

            # We delete the spaces the \n and \r that the email may add to our jwt token
            validation_header = validation_header.replace(" ", "")
            validation_header = validation_header.replace("\n", "")
            validation_header = validation_header.replace("\r", "")

            # We decode the Token
            data = jwt.decode(validation_header, public_key, algorithms=["RS256"])
            if data.get("sender", "") == sender and data.get("receiver", "") == receiver:
                return True
            return False

        except Exception as e:
            print(e)
            return False


class EmailAnalyzer:
    def __init__(self, mailbox, smtp_sender, user):
        self.mailbox = mailbox
        self.smtp_sender = smtp_sender
        self.user = user

        self.whitelist_expressions = WhiteListRegularExpression.query.filter(
            WhiteListRegularExpression.fk_user == user.id
        ).all()
        self.blacklist_expressions = BlackListRegularExpression.query.filter(
            BlackListRegularExpression.fk_user == user.id
        ).all()

        self.white_list = WhiteList.query.filter(WhiteList.fk_user == user.id).all()
        # We keep only the email
        self.white_list = [mail.email for mail in self.white_list]

        self.black_list = BlackList.query.filter(BlackList.fk_user == user.id).all()
        # We keep only the email
        self.black_list = [mail.email for mail in self.black_list]

        # key words expressions which are going to be considered as possible spam
        self.key_words_expressions = [BlackListRegularExpression(expression="^SPAM.*", expression_type="email_subject")]

    def analyse_mails(self, mails, is_unseen):
        """It checks the sender for each email from the list. If the sender is not in the white list it will do one of the
        following actions:
            - If the email is in the black list, it will delete it from the mailbox.
            - If the email is not in the black list, it will delete it from the mailbox, save it in a repository as an .eml file,
              save some specific data in the database and send an email to the sender with the captcha.
        """
        for mail in mails:
            sender = self.mailbox.get_sender(mail)
            sender = sender.strip(">").split("<")[-1]
            email_subject = self.mailbox.get_subject(mail)
            history = History(
                fk_user=self.user.id,
                email_sender=sender,
                email_subject=email_subject,
            )
            if sender == self.user.email:
                history.reason = "user_email"
                if is_unseen:
                    # We mark the email as unseen since the user has not read it yet
                    self.mailbox.mark_as_unseen(mail)
            elif sender == APP_EMAIL:
                history.reason = "app_email"
                if is_unseen:
                    # We mark the email as unseen since the user has not read it yet
                    self.mailbox.mark_as_unseen(mail)
            elif fulfils_expression(sender, email_subject, self.key_words_expressions):
                history.reason = "quarantine_keyword"
                self._save_email_in_quarantine(mail, sender, history)
            elif sender in self.white_list:
                history.reason = "white_list"
                if is_unseen:
                    # We mark the email as unseen since the user has not read it yet
                    self.mailbox.mark_as_unseen(mail)
            elif sender in self.black_list:
                # We delete the email
                history.reason = "black_list"
                self.mailbox.delete(mail)
                print("Deleting")
            elif fulfils_expression(sender, email_subject, self.whitelist_expressions):
                history.reason = "white_list_expression"
                if is_unseen:
                    # We mark the email as unseen since the user has not read it yet
                    self.mailbox.mark_as_unseen(mail)
            elif fulfils_expression(sender, email_subject, self.blacklist_expressions):
                # We delete the email
                history.reason = "black_list_expression"
                self.mailbox.delete(mail)
                print("Deleting")
            else:
                # we add the email to the quarantine
                history.reason = "quarantine"
                self._save_email_in_quarantine(mail, sender, history)

            db.session.add(history)
            db.session.commit()

    def _save_email_in_quarantine(self, mail, sender, history):
        """It deletes the email from the mailbox, saves it in the repository and in the database, and it sends an email
        to the sender with the link to the captcha that needs to be solved"""
        # We get all the content of the email
        emails_in_quarantine = (
            Quarantine.query.filter(Quarantine.fk_user == self.user.id).with_entities(Quarantine.email_id).all()
        )
        emails_in_quarantine = [mail[0] for mail in emails_in_quarantine]

        verify_url = os.environ.get("FRONTEND_ADDRESS") + "verify/{}"
        parameters = {
            "PERSON_NAME": self.user.full_name.title(),
            "VERIFY_URL": "",
        }

        message = self.mailbox.get_mail(mail)
        if message.message_id() in emails_in_quarantine:  # TODO: delete this if
            history.reason = "restored_email"
            print("(Provisional) Message already in quarantine")
            self.mailbox.mark_as_unseen(mail)
            return

        if check_validation_header(message, self.user.email, sender):
            history.reason = "restored_email"
            print("(Provisional) Message already in quarantine")
            self.mailbox.mark_as_unseen(mail)
            return

        directory_path = os.path.join(BASE_PATH, self.user.email)
        # We verify the user has a directory. If he does not have, we create one
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)

        message_id = message.message_id()
        if not message_id:
            message_id = f"{datetime.datetime.now()}"
        path = os.path.join(directory_path, message_id + ".eml")

        # we save the email in the repository
        size = message.save(path)
        print(
            "Message from {} with id {} and size {}, was deleted and saved in {}\n".format(
                sender, message_id, size, path
            )
        )

        # we save some information in the database
        quarantined_email = Quarantine(
            fk_user=self.user.id,
            email_sender=sender,
            email_subject=message.subject(),
            email_size=size,
            email_id=message_id,
            client_id=None,
        )
        db.session.add(quarantined_email)
        db.session.commit()

        # We delete the email
        self.mailbox.delete(mail)

        # we send an email with the captcha
        parameters["VERIFY_URL"] = verify_url.format(quarantined_email.id)
        header = create_header(self.user.email, sender)
        self.smtp_sender.send_message(
            self.user.email,
            sender,
            "RE: " + message.subject(),
            MessageCreator.create_message_template(TEMPLATE_NAME, parameters),
            validation_header=header,
        )
