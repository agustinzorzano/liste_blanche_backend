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
import threading

load_dotenv()

BASE_PATH = os.environ.get("BASE_PATH")
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_imap_server(user_email):
    """Returns the IMAP server depending on the email"""
    servers = {"gmx.com": "imap.gmx.com", "gmail.com": "imap.gmail.com"}
    return servers[user_email.split("@")[1]]


def get_smtp_server(user_email):
    """Returns the SMTP server depending on the email"""
    servers = {"gmx.com": "mail.gmx.com", "gmail.com": "smtp.gmail.com"}
    return servers[user_email.split("@")[1]]


def restore_emails(mailbox, user):
    """Restores the emails that need to be restored"""
    mails_to_restore = Quarantine.query.filter(
        Quarantine.fk_user == user.id,
        Quarantine.to_restore == True,
        Quarantine.was_restored == False,
    ).all()
    for mail in mails_to_restore:
        path = os.path.join(BASE_PATH, user.email, mail.email_id + ".eml")
        if os.path.exists(path):
            file = open(path)
            message = Email(file)
            mailbox.append(message)
            file.close()
            os.remove(path)
            mail.was_restored = True
    if mails_to_restore:
        db.session.commit()


def email_event_reader(user_email, thread_list, event, lock):
    """Starts the idle event with the mailbox and waits for the arrive of new emails. When a new email arrives, it
    notifies it with an event"""
    print("get user thread")
    user = User.query.filter(User.email == user_email).first()
    if user is None:
        return
    password = Encryptor.decrypt(user.email_password)
    print("connect mailbox thread")
    # TODO: add an event to notify the other thread if this one finishes
    mailbox = Imap(user_email, password)
    mailbox.select("inbox")

    mailbox.start_idle()
    while True:
        message = mailbox.readline()
        print(message)
        if "EXISTS" not in message and "RECENT" not in message:
            continue
        lock.acquire()
        thread_list.append(message)
        event.set()
        lock.release()


def scan_email(mailbox, smtp_sender, user):
    """Scans the last emails received"""
    last_uid = user.last_uid_scanned
    if last_uid == 0:
        # The mailbox has never been scanned
        last_uid = 1

    # We get all the unseen and seen emails whose uid is greater than last_uid_scanned
    unseen_emails = mailbox.search_unseen(user.created_at, last_uid)
    seen_emails = mailbox.search_seen(user.created_at, last_uid)
    print(unseen_emails)
    print(seen_emails)

    # We ignore the last scanned mail
    if unseen_emails[0::-1] == [str(user.last_uid_scanned)]:
        unseen_emails.pop(0)
    if seen_emails[0::-1] == [str(user.last_uid_scanned)]:
        seen_emails.pop(0)

    print(unseen_emails)
    print(seen_emails)

    mails_to_scan = len(unseen_emails) + len(seen_emails)

    if mails_to_scan > 0:
        email_analyzer = EmailAnalyzer(mailbox, smtp_sender, user)
        email_analyzer.analyse_mails(seen_emails, False)
        email_analyzer.analyse_mails(unseen_emails, True)

        # we get the greatest uid scanned
        last_scanned_id = max([int(i) for i in (unseen_emails[-1:] or [0]) + (seen_emails[-1:] or [0])])
        user.last_uid_scanned = last_scanned_id
        db.session.commit()


def main():
    if len(sys.argv) < 2:
        return
    user_email = sys.argv[1]
    event = threading.Event()
    lock = threading.Lock()
    thread_list = []
    thread = threading.Thread(target=email_event_reader, args=(user_email, thread_list, event, lock))
    print("before thread")
    thread.start()
    while True:
        print("get user main")
        user = User.query.filter(User.email == user_email).first()
        if user is None:
            break
        password = user.email_password  # TODO: Decrypt the password
        print("connect mailbox main")
        mailbox = Imap(user.email, password)
        smtp_sender = Smtp(user.email, password)
        # TODO: add an event to notify the other thread if this one finishes
        mailbox.select("inbox")
        # TODO: add the mechanism to reconnect to the mailbox and smtp if it is necessary
        while True:
            # We wait 2 minutes for at most 2 minutes to receive an event. If we receive an event, we scan the mailbox
            # and then we restore the emails. If no event arrives after 2 minutes, we restore the emails and then we
            # wait again.
            print("waiting for an event")
            event_is_set = event.wait(120)
            if event_is_set and thread_list:
                lock.acquire()
                event.clear()
                thread_list.clear()
                lock.release()
                print("analyse email")
                scan_email(mailbox, smtp_sender, user)

            # We restore the emails that need to be restored
            restore_emails(mailbox, user)
    thread.join()


main()


# from spam.email import Email
# file = open("<path>")
# m = Email(file)
# mailbox.append(m)
# file.close()
# return
