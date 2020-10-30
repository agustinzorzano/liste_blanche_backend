import sys
import os
import datetime
from spam.models import Quarantine, User
from spam.message_creator import MessageCreator
from spam.smtp import Smtp
from dotenv import load_dotenv

load_dotenv()
TEMPLATE_NAME = 'summary_email.html'


def main():
    if len(sys.argv) < 2:
        return
    user_email = sys.argv[1]
    user = User.query.filter(User.email == user_email).first()
    if user is None:
        return
    today = datetime.date.today()
    initial_date = today + datetime.timedelta(-1)
    mails = Quarantine.query.filter(Quarantine.fk_user == user.id, Quarantine.created_at >= initial_date).all()
    initial_date = initial_date.strftime("%d/%m/%Y %H:%M")
    final_date = today.strftime("%d/%m/%Y %H:%M")
    # TODO: USE a special email for this
    email_sender = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    smtp_sender = Smtp(os.getenv('EMAIL_HOST'))
    if not smtp_sender.login(email_sender, password):
        return
    parameters = {'PERSON_NAME': user.full_name, 'PERSON_EMAIL': user.email, 'mails': mails,
                  'initial_date': initial_date,
                  'final_date': final_date}
    message = MessageCreator.create_message_template(TEMPLATE_NAME, parameters)

    smtp_sender.send_message(email_sender, user_email, "Summary {}".format(final_date), message)


main()
