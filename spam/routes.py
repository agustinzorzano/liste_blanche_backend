from flask import request, jsonify
from spam import app, db
from spam.models import User, WhiteList, WhiteListRegularExpression, Quarantine
from spam.imap import Imap
from spam.email import Email
from spam.encryptor import Encryptor
from spam.exceptions import ApiError
import os

BASE_PATH = os.environ.get("BASE_PATH")


@app.route('/user/<user_id>/email/restoration', methods=['POST'])
def restore_emails(user_id):
    """Endpoint to restore emails to the mailbox"""
    user = User.query.filter(User.id == user_id).first()
    if user is None:
        return "error", 404
    password = Encryptor.decrypt(user.email_password)
    mailbox = Imap(user.email, password)
    # if not mailbox.login(user.email, password):
    #     return "error", 404
    mails_to_restore = Quarantine.query.filter(Quarantine.fk_user == user.id,
                                               Quarantine.to_restore == True,
                                               Quarantine.was_restored == False).all()

    for mail in mails_to_restore:
        path = os.path.join(BASE_PATH, user.email, mail.email_id + '.eml')
        if os.path.exists(path):
            file = open(path)
            message = Email(file)
            mailbox.append(message)
            file.close()
            os.remove(path)
            mail.was_restored = True
    if mails_to_restore:
        db.session.commit()

    return '', 204


@app.route('/connection', methods=['POST'])
def test_connection():
    """Endpoint to test the IMAP connection with the mailbox"""
    if not request.json:
        return "error", 404
    data = request.get_json()
    email = data.get("email")
    # password = data.get("password")
    password = Encryptor.decrypt(data.get("password"))
    if not email or not password:
        return "error", 404

    Imap(email, password)
    # if not mailbox.login(email, password):
    #     return "error", 404
    return '', 204


@app.errorhandler(ApiError)
def handle_error(error):
    """Error handler. If an exception is raised and not caught by an endpoint, this function will handle it"""
    status_code = error.status_code
    # response = response_error(error, status_code)
    # return jsonify(response), status_code
    return '', status_code
