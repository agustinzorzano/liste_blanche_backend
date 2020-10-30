import smtplib
import logging
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Smtp:
    def __init__(self, server='mail.gmail.com'):
        logging.info("Connecting to the server...")
        self.mail = smtplib.SMTP_SSL(server)  # It takes time to connect to a server like gmail
        logging.info("Connection accomplished")

    def login(self, user_email, password):
        try:
            self.mail.login(user_email, password)
            return True
        except Exception:
            return False

    def send_message(self, sender, destination, subject, message):
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = destination
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'html'))
        self.mail.send_message(msg)


class Message:
    @staticmethod
    def create_message_template(path, parameters):
        with open(path, 'r', encoding='utf-8') as template_file:
            message = template_file.read()
        message = Template(message)
        return message.substitute(parameters)


# aa = Smtp('mail.gmx.com')
# aa.login('aguszorza@gmx.com', 'Agustin95!')
# message1 = Message.create_message_template('./templates/captcha_email.html', {'PERSON_NAME': "agustin zorzano".title()})#Template(message1)
# aa.send_message('aguszorza@gmx.com', 'aguszorza@gmail.com', "This is TEST", message1)
