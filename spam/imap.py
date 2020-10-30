import imaplib
import email
import logging
from spam.email import Email


class Imap:
    def __init__(self, server='imap.gmail.com'):
        logging.info("Connecting to the server...")
        self.mail = imaplib.IMAP4_SSL(server)  # It takes time to connect to a server like gmail
        logging.info("Connection accomplished")

    def login(self, user_email, password):
        try:
            self.mail.login(user_email, password)
            return True
        except imaplib.IMAP4.error:
            return False

    def list(self):
        return self.mail.list()

    def select(self, folder='inbox'):
        self.mail.select(folder)

    def get_mail(self, email_id):
        typ, data = self.mail.fetch(email_id.encode(), '(RFC822)')
        return Email(data)

    def get_sender(self, email_id):
        typ, data = self.mail.fetch(email_id.encode(), '(BODY[HEADER.FIELDS (From)])')
        return email.message_from_string(data[0][1].decode())['from']

    def search_unseen(self):
        return self.mail.search(None, '(UNSEEN)')

    def search_seen(self):
        return self.mail.search(None, 'SEEN')

    def search_all(self):
        return self.mail.search(None, '(all)')

    def mark_as_unseen(self, email_ids):
        if type(email_ids) != list:
            email_ids = [email_ids]
        for mail in email_ids:
            self.mail.store(mail, '-FLAGS', '(\\Seen)')
        self.mail.expunge()

    def delete(self, email_ids):
        if type(email_ids) != list:
            email_ids = [email_ids]
        for mail in email_ids:
            self.mail.store(mail, '+FLAGS', '\\Deleted')
        self.mail.expunge()
