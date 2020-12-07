from spam import db
from sqlalchemy import text


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120))
    # username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    email_password = db.Column(db.String(512))
    password = db.Column(db.String(255))
    last_uid_scanned = db.Column(db.Integer, default=0, server_default=text("0"))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), default=db.func.now())

    def __repr__(self):
        return '<User {}>'.format(self.username)


class WhiteList(db.Model):
    __tablename__ = 'white_list'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"))


class WhiteListRegularExpression(db.Model):
    __tablename__ = 'white_list_regular_expression'
    # ex: \S+@gmail[.]com
    id = db.Column(db.Integer, primary_key=True)
    expression = db.Column(db.String(120))
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"))


class BlackList(db.Model):
    __tablename__ = 'black_list'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"))


class BlackListRegularExpression(db.Model):
    __tablename__ = 'black_list_regular_expression'
    id = db.Column(db.Integer, primary_key=True)
    expression = db.Column(db.String(120))
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"))


class Quarantine(db.Model):
    __tablename__ = 'quarantine'
    # TODO: check the types and sizes
    id = db.Column(db.Integer, primary_key=True)
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"))
    email_sender = db.Column(db.String(120))
    email_subject = db.Column(db.String(120))
    email_size = db.Column(db.Integer)
    email_id = db.Column(db.String(120))
    to_eliminate = db.Column(db.Boolean, default=False, server_default=text("false"))
    to_restore = db.Column(db.Boolean, default=False, server_default=text("false"))
    was_restored = db.Column(db.Boolean, default=False, server_default=text("false"))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), default=db.func.now())
