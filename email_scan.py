import sys
import os
import logging
from spam import db
from spam.imap import Imap
from spam.models import User, WhiteList, Quarantine
from spam.smtp import Smtp
from spam.message_creator import MessageCreator
from dotenv import load_dotenv
load_dotenv()

BASE_PATH = os.environ.get("BASE_PATH")
TEMPLATE_NAME = 'captcha_email.html'
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def analyse_mails(mailbox, smtp_sender, white_list, mails, is_unseen, user):
    emails_in_quarantine = Quarantine.query.filter(Quarantine.fk_user == user.id).with_entities(Quarantine.email_id).all()
    emails_in_quarantine = [mail[0] for mail in emails_in_quarantine]
    parameters = {'PERSON_NAME': user.full_name.title()}
    for mail in mails:
        sender = mailbox.get_sender(mail)
        sender = sender.strip('>').split('<')[-1]
        if sender not in white_list:
            message = mailbox.get_mail(mail)
            if message.message_id() in emails_in_quarantine:  # TODO: delete this if
                print("(Provisional) Message already in quarantine")
                continue
            path = os.path.join(BASE_PATH, user.email, message.message_id() + '.eml')
            # we save the email in the directory
            size = message.save(path)
            logging.info('Message from {} with id {} and size {}, was deleted and saved in {}\n'.format(sender, message.message_id(), size, path))
            # mailbox.delete(mail)
            # we save some information in the database
            quarantined_email = Quarantine(fk_user=user.id, email_sender=sender, email_subject=message.subject(),
                                           email_size=size, email_id=message.message_id())
            db.session.add(quarantined_email)
            db.session.commit()
            # we send an email with the captcha
            smtp_sender.send_message(user.email, sender, 'RE: ' + message.subject(),
                                     MessageCreator.create_message_template(TEMPLATE_NAME, parameters))
        elif is_unseen:
            mailbox.mark_as_unseen(mail)


def get_imap_server(user_email):
    servers = {'gmx.com': 'imap.gmx.com', 'gmail.com': 'imap.gmail.com'}
    return servers[user_email.split('@')[1]]


def get_smtp_server(user_email):
    servers = {'gmx.com': 'mail.gmx.com', 'gmail.com': 'smtp.gmail.com'}
    return servers[user_email.split('@')[1]]


def main():
    if len(sys.argv) < 2:
        return
    user_email = sys.argv[1]
    user = User.query.filter(User.email == user_email).first()
    if user is None:
        return
    password = user.email_password  # TODO: Decrypt the password
    mailbox = Imap(get_imap_server(user.email))
    smtp_sender = Smtp(get_smtp_server(user.email))
    if not mailbox.login(user_email, password):
        return
    if not smtp_sender.login(user_email, password):
        return
    mailbox.select('inbox')
    white_list = WhiteList.query.filter(WhiteList.fk_user == user.id).all()
    white_list = [mail.email for mail in white_list]
    unseen_emails = mailbox.search_unseen(user.last_uid_scanned)
    seen_emails = mailbox.search_seen(user.last_uid_scanned)
    analyse_mails(mailbox, smtp_sender, white_list, seen_emails, False, user)
    analyse_mails(mailbox, smtp_sender, white_list, unseen_emails, True, user)
    mails_scanned = len(unseen_emails) + len(seen_emails) - 1
    if mails_scanned < 0:
        mails_scanned = 0
    user.last_uid_scanned += mails_scanned
    db.session.commit()


main()
