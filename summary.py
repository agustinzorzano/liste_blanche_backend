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
