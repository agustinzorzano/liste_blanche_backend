import imaplib
import email
import logging
import time
from functools import wraps
from spam.email import Email
from spam.exceptions import ImapError


def get_imap_server(user_email):
    """Returns the IMAP server depending on the email"""
    servers = {
        "gmx.com": "imap.gmx.com",
        "gmail.com": "imap.gmail.com",
        "laposte.net": "imap.laposte.net",
    }
    return servers[user_email.split("@")[1]]


def handle_error(function):
    """Decoration which will execute the function and return its value. If there is an error,
    it will reconnect to the server and try another time to execute the function"""

    @wraps(function)
    def decorated_function(*args, **kwargs):
        try:
            # We execute the method
            return function(*args)
        except imaplib.IMAP4.error:
            # If there is an error we reconnect and we re-execute the method
            try:
                args[0]._connection()
                return function(*args)
            except imaplib.IMAP4.error:
                # The reconnection did not solve the problem
                raise ImapError

    return decorated_function


class Imap:
    def __init__(self, user_email, password):
        self.user_email = user_email
        self.password = password
        self._connection()

    def _connection(self):
        """Connects to the IMAP server and logs in with the email and password"""
        try:
            logging.info("Connecting to the server...")
            self.mail = imaplib.IMAP4_SSL(
                get_imap_server(self.user_email)
            )  # It takes time to connect to a server like gmail
            self.mail.login(self.user_email, self.password)
            logging.info("Connection accomplished")
        except imaplib.IMAP4.error:
            raise ImapError

    def list(self):
        return self.mail.list()

    @handle_error
    def select(self, folder="inbox"):
        """Selects the current mailbox folder"""
        self.mail.select(folder)

    @handle_error
    def get_mail(self, email_id):
        """Returns the email content of the email with the id email_id"""
        # typ, data = self.mail.fetch(email_id.encode(), '(RFC822)')
        typ, data = self.mail.uid("fetch", email_id, "(RFC822)")
        return Email(data)

    @handle_error
    def get_sender(self, email_id):
        """Returns the sender of the email with the id email_id"""
        # typ, data = self.mail.fetch(email_id.encode(), '(BODY[HEADER.FIELDS (From)])')
        typ, data = self.mail.uid("fetch", email_id, "(BODY[HEADER.FIELDS (From)])")
        return email.message_from_string(data[0][1].decode())["from"]

    @handle_error
    def _search(self, flags, since_date, initial_uid=1):
        """Returns a list with the emails whose uid is greater than initial_uid and were received after the date since_date"""
        # return self.mail.search(None, '({} SINCE {} UID {}:*)'.format(flags, since_date.strftime("%d-%b-%Y"), initial_uid))[1][0].decode().split()
        return (
            self.mail.uid("search", None, f'({flags} SINCE {since_date.strftime("%d-%b-%Y")} UID {initial_uid}:*)',)[
                1
            ][0]
            .decode()
            .split()
        )

    def search_unseen(self, since_date, initial_uid=1):
        """Returns a list with the unseen emails whose uid is greater than initial_uid and
        were received after the date since_date"""
        return self._search("UNSEEN", since_date, initial_uid)
        # return self.mail.search(None, '(UNSEEN UID {}:*)'.format(initial_uid))[1][0].decode().split()

    def search_seen(self, since_date, initial_uid=1):
        """Returns a list with the seen emails whose uid is greater than initial_uid and
        were received after the date since_date"""
        return self._search("SEEN", since_date, initial_uid)
        # return self.mail.search(None, '(SEEN UID {}:*)'.format(initial_uid))[1][0].decode().split()

    def search_all(self, since_date, initial_uid=1):
        """Returns a list with all the emails whose uid is greater than initial_uid and
        were received after the date since_date"""
        return self._search("all", since_date, initial_uid)

    @handle_error
    def mark_as_unseen(self, email_ids):
        """It marks an email or a list of emails as unseen"""
        if type(email_ids) != list:
            email_ids = [email_ids]
        for mail in email_ids:
            self.mail.uid("store", mail, "-FLAGS", "(\\Seen)")
        self.mail.expunge()

    @handle_error
    def delete(self, email_ids):
        """Deletes an email from the mailbox"""
        if type(email_ids) != list:
            email_ids = [email_ids]
        for mail in email_ids:
            self.mail.uid("store", mail, "+FLAGS", "\\Deleted")
        self.mail.expunge()

    @handle_error
    def append(self, message):
        """Adds an email to the mailbox"""
        # We reset the date so that the reception date appears as the current date
        # TODO: confirm the reset date
        message.reset_date()
        self.mail.append(
            "INBOX",
            "",
            imaplib.Time2Internaldate(time.time()),
            message.str().encode("utf-8"),
        )

    def start_idle(self):
        """Starts the IDLE mode with the IMAP server"""
        self.mail.send(("%s IDLE\r\n" % self.mail._new_tag()).encode())

    def readline(self):
        """Waits until the mailbox sends a new message and returns this message"""
        return self.mail.readline().decode()
