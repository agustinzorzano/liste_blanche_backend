from spam import app, db
from spam.models import User, WhiteList, WhiteListRegularExpression


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
