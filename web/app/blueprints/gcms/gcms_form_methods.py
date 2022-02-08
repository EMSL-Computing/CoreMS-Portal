
import json

from corems.encapsulation.factory.processingSetting import GasChromatographSetting, CompoundSearchSettings
from flask_login import  current_user
from werkzeug.datastructures import MultiDict

from app import db
from app.models.gcms_model import GCMS_Parameters
from app.forms.gcms_forms import CompoundSearchSettingsForm, GasChromatographSettingForm

def allowed_gcms_file(filename, calibration=False):

    ALLOWED_EXTENSIONS = set(['cdf'])

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_gcms_parameters():

    # no parameters found in the database creating one
    if not current_user.gcms_parameters.first():

        compound_search = CompoundSearchSettings()
        gcms_signal = GasChromatographSetting()

        data = {'user_id': current_user.id,
                'name': 'default',
                'basic_parameters': json.dumps(compound_search.__dict__),
                'advanced_parameters': json.dumps(gcms_signal.__dict__),
                }

        gcms_parameters = GCMS_Parameters(**data)
        db.session.add(gcms_parameters)
        db.session.commit()
        return gcms_parameters

    else: return current_user.gcms_parameters.order_by(GCMS_Parameters.id.desc()).first()

def populate_gcms_compound_search_form(gcms_parameters=None):

    if not gcms_parameters:

        gcms_parameters = check_gcms_parameters()

    parameter_data = gcms_parameters.basic_parameters_dict

    form = CompoundSearchSettingsForm(MultiDict(parameter_data))

    return form

def populate_gcms_signal_form(gcms_parameters=None):

    if not gcms_parameters:

        gcms_parameters = check_gcms_parameters()

    parameter_data = gcms_parameters.advanced_parameters_dict

    form = GasChromatographSettingForm(MultiDict(parameter_data))

    return form
