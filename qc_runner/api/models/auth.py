
import json

import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy as sa
from api.sqlalchemy import Base

class User(Base):

    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String(100))
    password = sa.Column(sa.String)
    username = sa.Column(sa.String(100))
    api_key = sa.Column(sa.String)
    first_name = sa.Column(sa.String(100))
    last_name = sa.Column(sa.String(100))

    # relationship for group access
    access_groups = sa.orm.relationship("AccessLink", back_populates="user")

    # relationship for user owned - legacy transition code
    ftms_data = sa.orm.relationship('FTMS_Data', backref='user', lazy='dynamic')
    ftms_parameters = sa.orm.relationship('FTMS_Parameters', backref='user', lazy='dynamic')
    ftms_results = sa.orm.relationship('FTMS_Result', backref='user', lazy='dynamic')

    gcms_data = sa.orm.relationship('GCMS_Data', backref='user', lazy='dynamic')
    gcms_parameters = sa.orm.relationship('GCMS_Parameters', backref='user', lazy='dynamic')
    gcms_results = sa.orm.relationship('GCMS_Result', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.first_name)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

class AccessGroup(Base):

    __tablename__ = 'accessGroup'

    id = sa.Column(sa.Integer, primary_key=True)

    name = sa.Column(sa.String(100), unique=True)

    users = sa.orm.relationship("AccessLink", back_populates="access_group")

    ftms_all_data = sa.orm.relationship("FTMS_DataAccessLink", back_populates="access_group")

    gcms_all_data = sa.orm.relationship("GCMS_DataAccessLink", back_populates="access_group")

    def __repr__(self):
        return '<AccessGroup, name: {}, id: {}>'.format(self.name, self.id)

class AccessLink(Base):

    __tablename__ = 'accessLink'
    __table_args__ = (sa.sql.schema.UniqueConstraint('access_id', 'user_id', name='unique_access_link'), )

    access_id = sa.Column(sa.Integer, sa.ForeignKey('accessGroup.id'), primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), primary_key=True)

    user = sa.orm.relationship("User", back_populates="access_groups")
    access_group = sa.orm.relationship("AccessGroup", back_populates="users")
