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
        """Tries to log in. Returns True if it succeeds"""
        try:
            self.mail.login(user_email, password)
            return True
        except imaplib.IMAP4.error:
            return False

    def list(self):
        return self.mail.list()

    def select(self, folder='inbox'):
        """Selects the current mailbox folder"""
        self.mail.select(folder)

    def get_mail(self, email_id):
        """Returns the email content of the email with the id email_id"""
        typ, data = self.mail.fetch(email_id.encode(), '(RFC822)')
        return Email(data)

    def get_sender(self, email_id):
        """Returns the sender of the email with the id email_id"""
        typ, data = self.mail.fetch(email_id.encode(), '(BODY[HEADER.FIELDS (From)])')
        return email.message_from_string(data[0][1].decode())['from']

    def _search(self, flags, since_date, initial_uid=1):
        """Returns a list with the emails whose uid is greater than initial_uid"""
        return self.mail.search(None, '({} SINCE {} UID {}:*)'.format(flags, since_date.strftime("%d-%b-%Y"), initial_uid))[1][0].decode().split()

    def search_unseen(self, since_date, initial_uid=1):
        """Returns a list with the unseen emails whose uid is greater than initial_uid"""
        return self._search('UNSEEN', since_date, initial_uid)
        # return self.mail.search(None, '(UNSEEN UID {}:*)'.format(initial_uid))[1][0].decode().split()

    def search_seen(self, since_date, initial_uid=1):
        """Returns a list with the seen emails whose uid is greater than initial_uid"""
        return self._search('SEEN', since_date, initial_uid)
        # return self.mail.search(None, '(SEEN UID {}:*)'.format(initial_uid))[1][0].decode().split()

    def search_all(self, since_date):
        return self._search('all', since_date)

    def mark_as_unseen(self, email_ids):
        """It marks an email or a list of emails as unseen"""
        if type(email_ids) != list:
            email_ids = [email_ids]
        for mail in email_ids:
            self.mail.store(mail, '-FLAGS', '(\\Seen)')
        self.mail.expunge()

    def delete(self, email_ids):
        """Deletes an email from the mailbox"""
        if type(email_ids) != list:
            email_ids = [email_ids]
        for mail in email_ids:
            self.mail.store(mail, '+FLAGS', '\\Deleted')
        self.mail.expunge()
