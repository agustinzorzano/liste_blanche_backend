import smtplib
import logging
from functools import wraps
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from spam.exceptions import SmtpError


def get_smtp_server(user_email):
    """Returns the SMTP server depending on the email"""
    servers = {'gmx.com': 'mail.gmx.com', 'gmail.com': 'smtp.gmail.com',
               'laposte.net': 'smtp.laposte.net'}
    return servers[user_email.split('@')[1]]


def handle_error(function):
    """Decoration which will execute the function and return its value. If there is an error,
    it will reconnect to the server and try another time to execute the function"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        try:
            # We execute the method
            return function(*args)
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPResponseException):
            # If there is an error we reconnect and we re-execute the method
            try:
                args[0]._connection()
                return function(*args)
            except smtplib.SMTPException:
                # The reconnection did not solve the problem
                raise SmtpError
    return decorated_function


class Smtp:
    def __init__(self, user_email, password):
        self.user_email = user_email
        self.password = password
        self._connection()

    def _connection(self):
        """Connects to the SMTP server and logs in with the email and password"""
        try:
            logging.info("Connecting to the server...")
            self.mail = smtplib.SMTP_SSL(get_smtp_server(self.user_email))  # It takes time to connect to a server like gmail
            self.mail.login(self.user_email, self.password)
            logging.info("Connection accomplished")
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPConnectError):
            raise SmtpError

    @handle_error
    def send_message(self, sender, destination, subject, message):
        """Sends an email with the subject and message given. The message needs to be an html template"""
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = destination
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'html'))
        self.mail.send_message(msg)
