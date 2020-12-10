import sys
import os
from spam import db
from spam.imap import Imap
from spam.models import User, Quarantine
from spam.encryptor import Encryptor
from spam.smtp import Smtp
from spam.email import Email
from spam.email_analyzer import EmailAnalyzer
from dotenv import load_dotenv
load_dotenv()

BASE_PATH = os.environ.get("BASE_PATH")
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_imap_server(user_email):
    """Returns the IMAP server depending on the email"""
    servers = {'gmx.com': 'imap.gmx.com', 'gmail.com': 'imap.gmail.com',
               'laposte.net': 'imap.laposte.net'}
    return servers[user_email.split('@')[1]]


def get_smtp_server(user_email):
    """Returns the SMTP server depending on the email"""
    servers = {'gmx.com': 'mail.gmx.com', 'gmail.com': 'smtp.gmail.com',
               'laposte.net': 'smtp.laposte.net'}
    return servers[user_email.split('@')[1]]


def restore_emails(mailbox, user):
    """Restores the emails that need to be restored"""
    mails_to_restore = Quarantine.query.filter(Quarantine.fk_user == user.id,
                                               Quarantine.to_restore == True,
                                               Quarantine.was_restored == False).all()
    for mail in mails_to_restore:
        path = os.path.join(BASE_PATH, user.email, mail.email_id + '.eml')
        if os.path.exists(path):
            file = open(path)
            message = Email(file)
            mailbox.append(message)
            file.close()
            os.remove(path)
            mail.was_restored = True
    if mails_to_restore:
        db.session.commit()


def main():
    if len(sys.argv) < 2:
        return
    user_email = sys.argv[1]
    user = User.query.filter(User.email == user_email).first()
    if user is None:
        return
    # We decrypt the password
    password = Encryptor.decrypt(user.email_password)
    mailbox = Imap(get_imap_server(user.email))
    smtp_sender = Smtp(get_smtp_server(user.email))
    if not mailbox.login(user_email, password):
        return
    if not smtp_sender.login(user_email, password):
        return
    mailbox.select('inbox')

    last_uid = user.last_uid_scanned
    if last_uid == 0:
        # The mailbox has never been scanned
        last_uid = 1

    # We get all the unseen and seen emails whose uid is greater than last_uid_scanned
    unseen_emails = mailbox.search_unseen(user.created_at, last_uid)
    seen_emails = mailbox.search_seen(user.created_at, last_uid)

    # We ignore the last scanned mail
    if unseen_emails[0::-1] == [str(user.last_uid_scanned)]:
        unseen_emails.pop(0)
    if seen_emails[0::-1] == [str(user.last_uid_scanned)]:
        seen_emails.pop(0)

    mails_to_scan = len(unseen_emails) + len(seen_emails)

    if mails_to_scan > 0:
        email_analyzer = EmailAnalyzer(mailbox, smtp_sender, user)
        email_analyzer.analyse_mails(seen_emails, False)
        email_analyzer.analyse_mails(unseen_emails, True)

        # we get the greatest uid scanned
        last_scanned_id = max([int(i) for i in (unseen_emails[-1:] or [0]) + (seen_emails[-1:] or [0])])
        user.last_uid_scanned = last_scanned_id
        db.session.commit()

    # We restore the emails that need to be restored
    # restore_emails(mailbox, user)


main()


# from spam.email import Email
# file = open("<path>")
# m = Email(file)
# mailbox.append(m)
# file.close()
# return
