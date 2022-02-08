from pathlib import Path
import pytz
import json

import pandas as pd
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from api.sqlalchemy import Base
from sqlalchemy.orm import deferred


class GCMS_DataAccessLink(Base):

    __tablename__ = 'gcmsDataAccessLink'
    __table_args__ = (sa.sql.schema.UniqueConstraint('access_id', 'gcms_data_id', name='unique_gcms_data_access_link'), )

    access_id = sa.Column(sa.Integer, sa.ForeignKey('accessGroup.id'), primary_key=True)
    gcms_data_id = sa.Column(sa.Integer, sa.ForeignKey('gcmsData.id'), primary_key=True)

    gcms_data = sa.orm.relationship("GCMS_Data", back_populates="access_groups")
    access_group = sa.orm.relationship("AccessGroup", back_populates="gcms_all_data")

class GCMS_Data(Base):

    __tablename__ = 'gcmsData'

    id = sa.Column(sa.Integer, primary_key=True)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

    access_groups = sa.orm.relationship("GCMS_DataAccessLink", back_populates="gcms_data")

    time_stamp = sa.Column(sa.DateTime, index=True, default=lambda:datetime.utcnow())

    filepath = sa.Column(sa.String)

    name = sa.Column(sa.String)

    modifier = sa.Column(sa.String(100))

    is_calibration = sa.Column(sa.Boolean, unique=False, default=False)

    gcms_results = sa.orm.relationship('GCMS_Result', backref='gcmsData', lazy='dynamic')

    def __repr__(self):
        return '<FTMS_Data {} path = {} >'.format(self.name, self.filepath)

    @property
    def pst_time_stamp(self):
        utc_now = pytz.utc.localize(self.time_stamp)
        pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
        return pst_now.strftime("%b %d %Y %H:%M:%S")

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

        if ext == '.cdf':
            return 'netCDF'

    def to_dict(self):
        return {'name': self.name, 'modifier': self.modifier,
                'is_calibration': self.is_calibration, 'id': self.id, 'filetype': self.filetype, 'suffix': self.suffix, 'pst_time_stamp': self.pst_time_stamp}

class GCMS_Result(Base):

    __tablename__ = 'gcmsResult'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    data_id = sa.Column(sa.Integer, sa.ForeignKey('gcmsData.id'))

    time_stamp = sa.Column(sa.DateTime, index=True, default=lambda:datetime.utcnow())

    name = sa.Column(sa.String)
    modifier = sa.Column(sa.String)

    status = sa.Column(sa.String(30), default="Unknown")
    stats = sa.Column(JSONB)

    rt = deferred(sa.Column(sa.ARRAY(sa.Float)))
    tic = deferred(sa.Column(sa.ARRAY(sa.Float)))

    mz = deferred(sa.Column(sa.ARRAY(sa.Float)))
    abundance = deferred(sa.Column(sa.ARRAY(sa.Float)))

    peaks = deferred(sa.Column(JSONB))
    data_table = deferred(sa.Column(JSONB))
    parameters = deferred(sa.Column(JSONB))

    def __repr__(self):

        return '<GCMS_Results {}>'.format(self.name)

    def to_dataframe(self):

        df = pd.read_json(self.data_table)
        df = df.sort_values(by=['Retention Time'])

        return df

    def peaks_to_dict(self):

        return json.loads(self.peaks)

    @property
    def deconvolved(self):

        parameters = json.loads(self.parameters)

        return parameters.get('CoreMSParameters').get("GasChromatograph").get("use_deconvolution")

    @property
    def pst_time_stamp(self):
        utc_now = pytz.utc.localize(self.time_stamp)
        pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
        return pst_now.strftime("%b %d %Y %H:%M:%S")

    @property
    def stats_formatted(self):

        if self.stats:
            stats_dict = json.loads(self.stats)

            if stats_dict.get("error"):
                return "Error : {}".format(stats_dict['error'])

            else:

                return "Peaks {} , Assigned {},  Unassigned {} , Unique Metabolites {}".format(stats_dict.get("total_number_peaks"), stats_dict.get("total_peaks_matched"),
                                                                                                                stats_dict.get("total_peaks_without_matches"), stats_dict.get("unique_metabolites"))
        else:
            return "Workflow stats will be available after the task has been completed"

class GCMS_Parameters(Base):

    __tablename__ = 'gcmsParameters'

   

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    name = sa.Column(sa.String(100))
    time_stamp = sa.Column(sa.DateTime, index=True, default=lambda:datetime.utcnow())

    basic_parameters = sa.Column(JSONB)
    advanced_parameters = sa.Column(JSONB)

    @property
    def basic_parameters_dict(cls):
        return json.loads(cls.basic_parameters)

    @property
    def advanced_parameters_dict(cls):
        return json.loads(cls.advanced_parameters)