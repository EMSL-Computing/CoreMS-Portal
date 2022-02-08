from datetime import datetime
from pathlib import Path
import pytz
import json

import yaml
import pandas as pd
from sqlalchemy.dialects.postgresql import JSONB

from app import db
from sqlalchemy.orm import deferred

class GCMS_DataAccessLink(db.Model):

    __tablename__ = 'gcmsDataAccessLink'
    __table_args__ = (db.UniqueConstraint('access_id', 'gcms_data_id', name='unique_gcms_data_access_link'), )

    access_id = db.Column(db.Integer, db.ForeignKey('accessGroup.id'), primary_key=True)
    gcms_data_id = db.Column(db.Integer, db.ForeignKey('gcmsData.id'), primary_key=True)

    gcms_data = db.relationship("GCMS_Data", back_populates="access_groups")
    access_group = db.relationship("AccessGroup", back_populates="gcms_all_data")

class GCMS_Data(db.Model):

    __tablename__ = 'gcmsData'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    access_groups = db.relationship("GCMS_DataAccessLink", back_populates="gcms_data")

    time_stamp = db.Column(db.DateTime, index=True, default=lambda: datetime.utcnow())

    filepath = db.Column(db.String)

    name = db.Column(db.String)

    modifier = db.Column(db.String(100))

    is_calibration = db.Column(db.Boolean, unique=False, default=False)

    gcms_results = db.relationship('GCMS_Result', backref='gcms_data', lazy='dynamic')

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

class GCMS_Result(db.Model):

    __tablename__ = 'gcmsResult'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    data_id = db.Column(db.Integer, db.ForeignKey('gcmsData.id'))

    time_stamp = db.Column(db.DateTime, index=True, default=lambda: datetime.utcnow())

    name = db.Column(db.String)
    modifier = db.Column(db.String)

    status = db.Column(db.String(30), default="Unknown")
    stats = db.Column(JSONB)

    rt = deferred(db.Column(db.ARRAY(db.Float)))
    tic = deferred(db.Column(db.ARRAY(db.Float)))

    mz = deferred(db.Column(db.ARRAY(db.Float)))
    abundance = deferred(db.Column(db.ARRAY(db.Float)))

    peaks = deferred(db.Column(JSONB))
    data_table = deferred(db.Column(JSONB))
    parameters = deferred(db.Column(JSONB))

    def __repr__(self):

        return '<FTMS_Results {}>'.format(self.name)

    @property
    def deconvolved(self):

        parameters = json.loads(self.parameters)

        print(parameters.keys())
        return parameters.get('CoreMSParameters').get("GasChromatograph").get("use_deconvolution")

    def to_dataframe(self):

        df = pd.read_json(self.data_table)
        df = df.sort_values(by=['Retention Time'])
        return df

    def peaks_to_dict(self):

        return json.loads(self.peaks)

    @property
    def pst_time_stamp(self):
        utc_now = pytz.utc.localize(self.time_stamp)
        pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
        return pst_now.strftime("%b %d %Y %H:%M:%S") 

    @property
    def parameters_yaml(self):

        return yaml.dump(json.loads(self.parameters), default_flow_style=False)

    @property
    def parameters_json(self):

        parsed = json.loads(self.arameters)
        output = json.dumps(parsed, sort_keys=False, indent=4, separators=(',', ': '))
        output.replace("\\", "\n")

        return output

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

class GCMS_Parameters(db.Model):

    __tablename__ = 'gcmsParameters'

    utc_now = pytz.utc.localize(datetime.utcnow())

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    time_stamp = db.Column(db.DateTime, index=True, default=lambda:datetime.utcnow())

    basic_parameters = db.Column(JSONB)
    advanced_parameters = db.Column(JSONB)

    @property
    def basic_parameters_dict(cls):
        return json.loads(cls.basic_parameters)

    @property
    def advanced_parameters_dict(cls):
        return json.loads(cls.advanced_parameters)
