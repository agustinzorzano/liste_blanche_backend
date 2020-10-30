from spam import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120))
    # username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    email_password = db.Column(db.String(255))
    password = db.Column(db.String(255))

    def __repr__(self):
        return '<User {}>'.format(self.username)


class WhiteList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"))


class BlackList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"))


class Quarantine(db.Model):
    # TODO: check the types and sizes
    id = db.Column(db.Integer, primary_key=True)
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"))
    email_sender = db.Column(db.String(120))
    email_subject = db.Column(db.String(120))
    email_size = db.Column(db.Integer)
    email_id = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
