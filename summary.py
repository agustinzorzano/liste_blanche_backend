import sys
import os
import datetime
from spam.models import Quarantine, User
from spam.message_creator import MessageCreator
from spam.smtp import Smtp
from dotenv import load_dotenv

load_dotenv()
TEMPLATE_NAME = "summary_email.html"


def main():
    if len(sys.argv) < 2:
        return
    user_email = sys.argv[1]
    user = User.query.filter(User.email == user_email).first()
    if user is None:
        return
    today = datetime.date.today()
    initial_date = today + datetime.timedelta(-1)
    # We get the all emails received since yesterday that are in the quarantine
    mails = Quarantine.query.filter(
        Quarantine.fk_user == user.id,
        Quarantine.created_at >= initial_date,
        Quarantine.to_restore == False,
        Quarantine.to_eliminate == False,
    ).all()
    initial_date = initial_date.strftime("%d/%m/%Y %H:%M")
    final_date = today.strftime("%d/%m/%Y %H:%M")
    # TODO: USE a special email for this
    email_sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    smtp_sender = Smtp(email_sender, password)
    # if not smtp_sender.login(email_sender, password):
    #     return
    # We set the parameters needed in the email template
    parameters = {
        "PERSON_NAME": user.full_name,
        "PERSON_EMAIL": user.email,
        "mails": mails,
        "initial_date": initial_date,
        "final_date": final_date,
    }
    message = MessageCreator.create_message_template(TEMPLATE_NAME, parameters)

    smtp_sender.send_message(email_sender, user.email, "Summary {}".format(final_date), message)


main()
