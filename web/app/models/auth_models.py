import datetime
from flask.globals import current_app
import jwt

import pandas as pd
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

class User(UserMixin, db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    password = db.Column(db.String)
    username = db.Column(db.String(100))
    api_key = db.Column(db.String)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    # relationship for group access
    access_groups = db.relationship("AccessLink", back_populates="user")

    # relationship for user owned - legacy transition code
    ftms_data = db.relationship('FTMS_Data', backref='user', lazy='dynamic')
    ftms_parameters = db.relationship('FTMS_Parameters', backref='user', lazy='dynamic')
    ftms_results = db.relationship('FTMS_Result', backref='user', lazy='dynamic')

    gcms_data = db.relationship('GCMS_Data', backref='user', lazy='dynamic')
    gcms_parameters = db.relationship('GCMS_Parameters', backref='user', lazy='dynamic')
    gcms_results = db.relationship('GCMS_Result', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.first_name)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def encode_auth_token(self):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'id': self.id,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'email': self.email,

            }

            return jwt.encode(
                payload,
                current_app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

class AccessGroup(db.Model):

    __tablename__ = 'accessGroup'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True)

    users = db.relationship("AccessLink", back_populates="access_group")

    ftms_all_data = db.relationship("FTMS_DataAccessLink", back_populates="access_group")

    gcms_all_data = db.relationship("GCMS_DataAccessLink", back_populates="access_group")

    def __repr__(self):
        return '<AccessGroup, name: {}, id: {}>'.format(self.name, self.id)

class AccessLink(db.Model):

    __tablename__ = 'accessLink'
    __table_args__ = (db.UniqueConstraint('access_id', 'user_id', name='unique_access_link'), )

    access_id = db.Column(db.Integer, db.ForeignKey('accessGroup.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    user = db.relationship("User", back_populates="access_groups")
    access_group = db.relationship("AccessGroup", back_populates="users")
