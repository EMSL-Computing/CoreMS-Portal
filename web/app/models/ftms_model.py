
from datetime import datetime
import json
import pytz
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import deferred
import yaml

from app import db

class FTMS_DataAccessLink(db.Model):

    __tablename__ = 'ftmsDataAccessLink'
    __table_args__ = (db.UniqueConstraint('access_id', 'ftms_data_id', name='unique_ftmsdata_access_link'), )

    access_id = db.Column(db.Integer, db.ForeignKey('accessGroup.id'), primary_key=True)
    ftms_data_id = db.Column(db.Integer, db.ForeignKey('ftmsData.id'), primary_key=True)

    ftms_data = db.relationship("FTMS_Data", back_populates="access_groups")
    access_group = db.relationship("AccessGroup", back_populates="ftms_all_data")

class FTMS_Data(db.Model):

    __tablename__ = 'ftmsData'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    access_groups = db.relationship("FTMS_DataAccessLink", back_populates="ftms_data")

    time_stamp = db.Column(db.DateTime, index=True, default=lambda: datetime.utcnow())

    filepath = db.Column(db.String)

    name = db.Column(db.String)

    modifier = db.Column(db.String(100))

    is_centroid = db.Column(db.Boolean, unique=False, default=False)

    ftms_results = db.relationship('FTMS_Result', backref='ftms_data', lazy='dynamic')

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

        if ext == '.txt' or ext == '.csv' or ext == '.pks':

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

class FTMS_Result(db.Model):

    __tablename__ = 'ftmsResults'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    data_id = db.Column(db.Integer, db.ForeignKey('ftmsData.id'))

    time_stamp = db.Column(db.DateTime, index=True, default=lambda: datetime.utcnow())

    name = db.Column(db.String)
    modifier = db.Column(db.String)

    status = db.Column(db.String(30), default="Unknown")
    stats = db.Column(JSONB)

    mz_raw = deferred(db.Column(db.ARRAY(db.Float)))
    abun_raw = deferred(db.Column(db.ARRAY(db.Float)))

    data_table = deferred(db.Column(JSONB))
    parameters = db.Column(JSONB)

    def __repr__(self):

        return '<FTMS_Results {}>'.format(self.name)

    def to_dataframe(self):

        return pd.read_json(self.data_table)

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

        parsed = json.loads(self.parameters)
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
                if stats_dict.get("method"):    
                    
                    return "Assigned {} , Unassigned {} , Percent Abundance {:.2f} %, RMS Error {:.2f} ppm, {} ".format(stats_dict.get("assigned"), stats_dict.get("unassigned"),
                                                                                                                   stats_dict.get("perc_abundance"), stats_dict.get("rms"), stats_dict.get("method"))
                else: 
        
                  return "Assigned {} , Unassigned {} , Percent Abundance {:.2f} %, RMS Error {:.2f} ppm".format(stats_dict.get("assigned"), stats_dict.get("unassigned"),
                                                                                                                   stats_dict.get("perc_abundance"), stats_dict.get("rms"))
        else:
            return "Workflow stats will be available after the task has been completed"

class FTMS_Parameters(db.Model):

    __tablename__ = 'ftmsParameters'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    time_stamp = db.Column(db.DateTime, index=True, default=lambda: datetime.utcnow())

    basic_parameters = db.Column(JSONB)
    input_data_parameters = db.Column(JSONB)
    advanced_parameters = db.Column(JSONB)
    ms_parameters = db.Column(JSONB)
    ms_peak_parameters = db.Column(JSONB)
    transient_parameters = db.Column(JSONB)

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
