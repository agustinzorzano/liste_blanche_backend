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
from spam import db
from spam.models import Quarantine, History
from spam.models import User
from sqlalchemy import or_
from dotenv import load_dotenv

load_dotenv()

BASE_PATH = os.environ.get("BASE_PATH")
EXPIRATION_DAYS = 40


def main():
    """It deletes all the emails of an specific user that have been in the quarantine for more than 40 days.
    It will delete the email file and the data from the database"""
    if len(sys.argv) < 2:
        return
    user_email = sys.argv[1]
    user = User.query.filter(User.email == user_email).first()
    if user is None:
        return
    limit_date = datetime.date.today() - datetime.timedelta(EXPIRATION_DAYS)
    emails_to_delete = Quarantine.query.filter(
        Quarantine.fk_user == user.id,
        or_(Quarantine.created_at < limit_date, Quarantine.to_eliminate == True),
    ).all()

    for mail in emails_to_delete:
        path = os.path.join(BASE_PATH, user.email, mail.email_id + ".eml")
        history = History(
            fk_user=user.id,
            email_sender=mail.email_sender,
            email_subject=mail.email_subject,
            reason="deleted_by_expiration",
        )
        if mail.to_eliminate:
            history.reason = "deleted_by_user"
        if os.path.exists(path):
            os.remove(path)
        db.session.add(history)
        db.session.delete(mail)
    if emails_to_delete:
        db.session.commit()


main()
