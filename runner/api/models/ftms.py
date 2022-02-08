
from pathlib import Path
from datetime import datetime
import pytz
import json

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import pandas as pd

from api.sqlalchemy import Base


class FTMS_DataAccessLink(Base):

    __tablename__ = 'ftmsDataAccessLink'
    __table_args__ = (sa.sql.schema.UniqueConstraint('access_id', 'ftms_data_id', name='unique_ftmsdata_access_link'), )

    access_id = sa.Column(sa.Integer, sa.ForeignKey('accessGroup.id'), primary_key=True)
    ftms_data_id = sa.Column(sa.Integer, sa.ForeignKey('ftmsData.id'), primary_key=True)

    ftms_data = sa.orm.relationship("FTMS_Data", back_populates="access_groups")
    access_group = sa.orm.relationship("AccessGroup", back_populates="ftms_all_data")

class FTMS_Data(Base):

    __tablename__ = 'ftmsData'

    id = sa.Column(sa.Integer, primary_key=True)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

    access_groups = sa.orm.relationship("FTMS_DataAccessLink", back_populates="ftms_data")

    time_stamp = sa.Column(sa.DateTime, index=True, default=lambda:datetime.utcnow())

    filepath = sa.Column(sa.String)

    name = sa.Column(sa.String)

    modifier = sa.Column(sa.String(100))

    is_centroid = sa.Column(sa.Boolean, unique=False, default=False)

    ftms_results = sa.orm.relationship('FTMS_Result', backref='ftmsData', lazy='dynamic')

    def __repr__(self):
        return '<FTMS_Data {} path = {} >'.format(self.name, self.filepath)

    @property
    def pst_time_stamp(self):
        utc_now = pytz.utc.localize(self.time_stamp)
        pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
        return pst_now

    @property
    def filename(self):
        return Path(self.filepath).name

    @property
    def directory(self):
        return Path(self.filepath).parent

    @property
    def suffix(self):
        return Path(self.filepath).suffix

    @property
    def filetype(self):

        ext = Path(self.filepath).suffix

        if ext == '.txt' or ext == '.csv'or ext == '.pks':

            if self.is_centroid: return 'centroid_masslist'
            else: return 'profile_masslist'

        if ext == '.d':
            return 'bruker_transient'

        if ext == '.raw':
            return 'thermo_reduced_profile'

        if ext == '.ref':
            return 'reference'

    def to_dict(self):
        return {'name': self.name, 'modifier': self.modifier,
                'id': self.id, 'filetype': self.filetype, 'suffix': self.suffix, 'pst_time_stamp': self.pst_time_stamp}

class FTMS_Result(Base):

    __tablename__ = 'ftmsResults'

    id = sa.Column(sa.Integer, primary_key=True)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    data_id = sa.Column(sa.Integer, sa.ForeignKey('ftmsData.id'))

    name = sa.Column(sa.String)
    time_stamp = sa.Column(sa.DateTime, index=True, default=lambda:datetime.utcnow())
    status = sa.Column(sa.String(30), default="Unknown")
    stats = sa.Column(JSONB)

    modifier = sa.Column(sa.String)

    mz_raw = sa.orm.deferred(sa.Column(sa.ARRAY(sa.Float)))
    abun_raw = sa.orm.deferred(sa.Column(sa.ARRAY(sa.Float)))

    data_table = sa.orm.deferred(sa.Column(JSONB))
    parameters = sa.orm.deferred(sa.Column(JSONB))

    def __repr__(self):
        return '<FTMS_DataTable {}>'.format(self.name)

    def to_dataframe(self):
        return pd.read_json(self.data_table)

    @property
    def pst_time_stamp(self):
        utc_now = pytz.utc.localize(self.time_stamp)
        pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
        return pst_now.strftime("%b %d %Y %H:%M:%S")

class FTMS_Parameters(Base):

    __tablename__ = 'ftmsParameters'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    name = sa.Column(sa.String(100))

    utc_now = pytz.utc.localize(datetime.utcnow())
    pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))

    time_stamp = sa.Column(sa.DateTime, index=True, default=lambda:datetime.utcnow())

    basic_parameters = sa.Column(JSONB)
    input_data_parameters = sa.Column(JSONB)
    advanced_parameters = sa.Column(JSONB)
    ms_parameters = sa.Column(JSONB)
    ms_peak_parameters = sa.Column(JSONB)
    transient_parameters = sa.Column(JSONB)

    @property
    def basic_parameters_dict(cls):
        return json.loads(cls.basic_parameters)

    @property
    def input_data_parameters_dict(cls):
        return json.loads(cls.input_data_parameters)

    @property
    def advanced_parameters_dict(cls):
        return json.loads(cls.advanced_parameters)

    @property
    def ms_parameters_dict(cls):
        return json.loads(cls.ms_parameters)

    @property
    def ms_peak_parameters_dict(cls):
        return json.loads(cls.ms_peak_parameters)

    @property
    def transient_parameters_dict(cls):
        return json.loads(cls.transient_parameters)
