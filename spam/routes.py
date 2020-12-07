from spam import app, db
from spam.models import User, WhiteList, WhiteListRegularExpression, Quarantine
from spam.imap import Imap
from spam.email import Email
import os

BASE_PATH = os.environ.get("BASE_PATH")

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/1')
def index2():
    a = User.query.filter(User.email == 'aguszorza@gmx.com').first()
    w = WhiteList(email='service@corp.gmx.com', fk_user=a.id)
    db.session.add(w)
    db.session.commit()
    return "Hello, World!"


@app.route('/2')
def index3():
    l = WhiteList.query.filter(WhiteList.fk_user == 2).with_entities(WhiteList.email).all()
    print(l)
    return 'ok'


@app.route('/3')
def index4():
    user = User.query.filter(User.email == 'aguszorza@gmx.com').first()
    user.full_name = 'Agustin Zorzano'
    db.session.commit()
    return 'ok'


@app.route('/4')
def index5():
    wle = WhiteListRegularExpression(expression="\S+@gmail[.]com", fk_user=1)
    db.session.add(wle)
    db.session.commit()
    return 'ok'


@app.route('/user/<user_id>/email/restoration', methods=['POST'])
def restore_emails(user_id):
    user = User.query.filter(User.id == user_id).first()
    if user is None:
        return "error", 404
    mailbox = Imap(get_imap_server(user.email))
    if not mailbox.login(user.email, user.email_password):
        return "error", 404
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


# TODO: Move it to the class IMAP
def get_imap_server(user_email):
    """Returns the IMAP server depending on the email"""
    servers = {'gmx.com': 'imap.gmx.com', 'gmail.com': 'imap.gmail.com',
               'laposte.net': 'imap.laposte.net'}
    return servers[user_email.split('@')[1]]
