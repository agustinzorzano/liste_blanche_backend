import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Smtp:
    def __init__(self, server='mail.gmail.com'):
        logging.info("Connecting to the server...")
        self.mail = smtplib.SMTP_SSL(server)  # It takes time to connect to a server like gmail
        logging.info("Connection accomplished")

    def login(self, user_email, password):
        """Tries to log in. Returns True if it succeeds"""
        try:
            self.mail.login(user_email, password)
            return True
        except Exception:
            return False

    def send_message(self, sender, destination, subject, message):
        """Sends an email with the subject and message given. The message needs to be an html template"""
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = destination
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'html'))
        self.mail.send_message(msg)
