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

from spam import db
from sqlalchemy import text


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(16), unique=True)
    full_name = db.Column(db.String(120))
    # username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    email_password = db.Column(db.String(512))
    password = db.Column(db.String(512))
    salt = db.Column(db.String(64))
    last_uid_scanned = db.Column(db.Integer, default=0, server_default=text("0"))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), default=db.func.now())

    def __repr__(self):
        return "<User {}>".format(self.email)


class WhiteList(db.Model):
    __tablename__ = "white_list"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"), nullable=False)


class WhiteListRegularExpression(db.Model):
    __tablename__ = "white_list_regular_expression"
    # ex: \S+@gmail[.]com
    id = db.Column(db.Integer, primary_key=True)
    user_expression = db.Column(db.String(120), nullable=False)  # The expression written by the user
    expression = db.Column(db.String(120), nullable=False)  # The regex expression we create from the user expression
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"), nullable=False)
    expression_type = db.Column(db.String(120), default="email_address", nullable=False)


class BlackList(db.Model):
    __tablename__ = "black_list"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"), nullable=False)


class BlackListRegularExpression(db.Model):
    __tablename__ = "black_list_regular_expression"
    id = db.Column(db.Integer, primary_key=True)
    user_expression = db.Column(db.String(120), nullable=False)  # The expression written by the user
    expression = db.Column(db.String(120), nullable=False)  # The regex expression we create from the user expression
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"), nullable=False)
    expression_type = db.Column(db.String(120), default="email_address", nullable=False)


class Quarantine(db.Model):
    __tablename__ = "quarantine"
    # TODO: check the types and sizes
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(16), nullable=True)
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"), nullable=False)
    email_sender = db.Column(db.String(120), nullable=False)
    email_subject = db.Column(db.String(120), nullable=False)
    email_size = db.Column(db.Integer)
    email_id = db.Column(db.String(120), nullable=False)
    to_eliminate = db.Column(db.Boolean, default=False, server_default=text("false"))
    to_restore = db.Column(db.Boolean, default=False, server_default=text("false"))
    was_restored = db.Column(db.Boolean, default=False, server_default=text("false"))
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        default=db.func.now(),
        nullable=False,
    )


class History(db.Model):
    __tablename__ = "history"
    id = db.Column(db.Integer, primary_key=True)
    fk_user = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="RESTRICT"), nullable=False)
    email_sender = db.Column(db.String(120), nullable=False)
    email_subject = db.Column(db.String(120), nullable=False)
    reason = db.Column(db.String(120), nullable=False)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        default=db.func.now(),
        nullable=False,
    )
