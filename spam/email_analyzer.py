import re
import os
from spam import db
from spam.models import (
    WhiteList,
    BlackList,
    WhiteListRegularExpression,
    BlackListRegularExpression,
    Quarantine,
)
from spam.message_creator import MessageCreator
from dotenv import load_dotenv

load_dotenv()

BASE_PATH = os.environ.get("BASE_PATH")
TEMPLATE_NAME = "captcha_email.html"


def fulfils_expression(mail, expressions):
    """It returns True if the email address matches one of the regular expressions in the expressions list"""
    for expression in expressions:
        if re.fullmatch(expression, mail):
            return True
    return False


class EmailAnalyzer:
    def __init__(self, mailbox, smtp_sender, user):
        self.mailbox = mailbox
        self.smtp_sender = smtp_sender
        self.user = user

        self.whitelist_expressions = (
            WhiteListRegularExpression.query.filter(WhiteListRegularExpression.fk_user == user.id)
            .with_entities(WhiteListRegularExpression.expression)
            .all()
        )
        # We keep only the regex expression
        self.whitelist_expressions = [mail[0] for mail in self.whitelist_expressions]

        self.blacklist_expressions = (
            BlackListRegularExpression.query.filter(BlackListRegularExpression.fk_user == user.id)
            .with_entities(BlackListRegularExpression.expression)
            .all()
        )
        # We keep only the regex expression
        self.blacklist_expressions = [mail[0] for mail in self.blacklist_expressions]

        self.white_list = WhiteList.query.filter(WhiteList.fk_user == user.id).all()
        # We keep only the email
        self.white_list = [mail.email for mail in self.white_list]

        self.black_list = BlackList.query.filter(BlackList.fk_user == user.id).all()
        # We keep only the email
        self.black_list = [mail.email for mail in self.black_list]

    def analyse_mails(self, mails, is_unseen):
        """It checks the sender for each email from the list. If the sender is not in the white list it will do one of the
        following actions:
            - If the email is in the black list, it will delete it from the mailbox.
            - If the email is not in the black list, it will delete it from the mailbox, save it in a repository as an .eml file,
              save some specific data in the database and send an email to the sender with the captcha.
        """
        emails_in_quarantine = (
            Quarantine.query.filter(Quarantine.fk_user == self.user.id).with_entities(Quarantine.email_id).all()
        )
        emails_in_quarantine = [mail[0] for mail in emails_in_quarantine]

        verify_url = os.environ.get("FRONTEND_ADDRESS") + "verify/{}"
        parameters = {
            "PERSON_NAME": self.user.full_name.title(),
            "VERIFY_URL": "",
        }
        for mail in mails:
            sender = self.mailbox.get_sender(mail)
            sender = sender.strip(">").split("<")[-1]
            if sender in self.white_list:
                if is_unseen:
                    # We mark the email as unseen since the user has not read it yet
                    self.mailbox.mark_as_unseen(mail)
            elif sender in self.black_list:
                # We delete the email
                self.mailbox.delete(mail)
                print("Deleting")
            elif fulfils_expression(sender, self.whitelist_expressions):
                if is_unseen:
                    # We mark the email as unseen since the user has not read it yet
                    self.mailbox.mark_as_unseen(mail)
            elif fulfils_expression(sender, self.blacklist_expressions):
                # We delete the email
                self.mailbox.delete(mail)
                print("Deleting")
            else:
                # we add the email to the quarantine
                # We get all the content of the email
                message = self.mailbox.get_mail(mail)
                if message.message_id() in emails_in_quarantine:  # TODO: delete this if
                    print("(Provisional) Message already in quarantine")
                    # mailbox.mark_as_unseen(mail)
                    continue

                directory_path = os.path.join(BASE_PATH, self.user.email)
                # We verify the user has a directory. If he does not have, we create one
                if not os.path.exists(directory_path):
                    os.mkdir(directory_path)

                path = os.path.join(directory_path, message.message_id() + ".eml")

                # we save the email in the repository
                size = message.save(path)
                print(
                    "Message from {} with id {} and size {}, was deleted and saved in {}\n".format(
                        sender, message.message_id(), size, path
                    )
                )

                # we save some information in the database
                quarantined_email = Quarantine(
                    fk_user=self.user.id,
                    email_sender=sender,
                    email_subject=message.subject(),
                    email_size=size,
                    email_id=message.message_id(),
                )
                db.session.add(quarantined_email)
                db.session.commit()

                # We delete the email
                self.mailbox.delete(mail)

                # we send an email with the captcha
                parameters["VERIFY_URL"] = verify_url.format(quarantined_email.id)
                self.smtp_sender.send_message(
                    self.user.email,
                    sender,
                    "RE: " + message.subject(),
                    MessageCreator.create_message_template(TEMPLATE_NAME, parameters),
                )
