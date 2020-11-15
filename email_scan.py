import sys
import os
import logging
import re
from spam import db
from spam.imap import Imap
from spam.models import User, WhiteList, Quarantine, WhiteListRegularExpression, BlackListRegularExpression, BlackList
from spam.smtp import Smtp
from spam.email import Email
from spam.message_creator import MessageCreator
from dotenv import load_dotenv
load_dotenv()

BASE_PATH = os.environ.get("BASE_PATH")
TEMPLATE_NAME = 'captcha_email.html'
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def fulfils_expression(mail, expressions):
    """It returns True if the email address matches one of the regular expressions in the expressions list"""
    for expression in expressions:
        if re.fullmatch(expression, mail):
            return True
    return False


def analyse_mails(mailbox, smtp_sender, white_list, mails, is_unseen, user):
    """It checks the sender for each email from the list. If the sender is not in the white list it will do one of the
    following actions:
        - If the email is in the black list, it will delete it from the mailbox.
        - If the email is not in the black list, it will delete it from the mailbox, save it in a repository as an .eml file,
          save some specific data in the database and send an email to the sender with the captcha.
    """
    emails_in_quarantine = Quarantine.query.filter(Quarantine.fk_user == user.id).with_entities(Quarantine.email_id).all()
    emails_in_quarantine = [mail[0] for mail in emails_in_quarantine]

    whitelist_expressions = WhiteListRegularExpression.query\
        .filter(WhiteListRegularExpression.fk_user == user.id)\
        .with_entities(WhiteListRegularExpression.expression).all()
    whitelist_expressions = [mail[0] for mail in whitelist_expressions]

    blacklist_expressions = BlackListRegularExpression.query\
        .filter(BlackListRegularExpression.fk_user == user.id)\
        .with_entities(BlackListRegularExpression.expression).all()
    blacklist_expressions = [mail[0] for mail in blacklist_expressions]

    black_list = BlackList.query.filter(BlackList.fk_user == user.id).all()
    black_list = [mail.email for mail in black_list]

    parameters = {'PERSON_NAME': user.full_name.title()}
    for mail in mails:
        sender = mailbox.get_sender(mail)
        sender = sender.strip('>').split('<')[-1]
        if sender in white_list:
            if is_unseen:
                # We mark the email as unseen since the user has not read it yet
                mailbox.mark_as_unseen(mail)
        elif sender in black_list:
            # We delete the email
            # mailbox.delete(mail)
            print("Deleting")
        elif fulfils_expression(sender, whitelist_expressions):
            if is_unseen:
                # We mark the email as unseen since the user has not read it yet
                mailbox.mark_as_unseen(mail)
        elif fulfils_expression(sender, blacklist_expressions):
            # We delete the email
            # mailbox.delete(mail)
            print("Deleting")
        else:
            # we add the email to the quarantine
            # We get all the content of the email
            message = mailbox.get_mail(mail)
            if message.message_id() in emails_in_quarantine:  # TODO: delete this if
                print("(Provisional) Message already in quarantine")
                # mailbox.mark_as_unseen(mail)
                continue
            path = os.path.join(BASE_PATH, user.email, message.message_id() + '.eml')
            # we save the email in the repository
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


def get_imap_server(user_email):
    """Returns the IMAP server depending on the email"""
    servers = {'gmx.com': 'imap.gmx.com', 'gmail.com': 'imap.gmail.com'}
    return servers[user_email.split('@')[1]]


def get_smtp_server(user_email):
    """Returns the SMTP server depending on the email"""
    servers = {'gmx.com': 'mail.gmx.com', 'gmail.com': 'smtp.gmail.com'}
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

    analyse_mails(mailbox, smtp_sender, white_list, seen_emails, False, user)
    analyse_mails(mailbox, smtp_sender, white_list, unseen_emails, True, user)
    mails_scanned = len(unseen_emails) + len(seen_emails)

    if mails_scanned > 0:
        # we get the greatest uid scanned
        last_scanned_id = max([int(i) for i in (unseen_emails[-1:] or [0]) + (seen_emails[-1:] or [0])])
        user.last_uid_scanned = last_scanned_id
        db.session.commit()
    # user.last_uid_scanned += mails_scanned
    # db.session.commit()

    # We restore the emails that need to be restored
    restore_emails(mailbox, user)


main()


# from spam.email import Email
# file = open("<path>")
# m = Email(file)
# mailbox.append(m)
# file.close()
# return
