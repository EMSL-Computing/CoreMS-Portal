import json

from flask_login import  current_user
from werkzeug.datastructures import MultiDict

from app.forms.fticr_forms import AdvancedFtmsSettingsForm, BasicFtmsSettingsForm
from app.forms.fticr_forms import FTMSSubmitJob, KendrickForm, MassSpecPeakSettingForm
from app.forms.fticr_forms import MassSpectrumSettingForm, TransientSettingForm, UsedAtom, DataInputSettingForm
from app import db
from app.models.ftms_model import FTMS_Parameters

from corems.encapsulation.factory.processingSetting import MassSpecPeakSetting, MassSpectrumSetting, \
                                                           MolecularFormulaSearchSettings, TransientSetting

def allowed_file(filename, calibration=False):

    if not calibration:
        ALLOWED_EXTENSIONS = set(['txt','csv', 'd', 'raw', 'pks'])

    else:
        ALLOWED_EXTENSIONS = set(['ref'])

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_input_type_label(filename):

    ext = filename.rsplit('.', 1)[1].lower()

    if ext == 'txt':
        return 'masslist'

    if ext == 'd':
        return 'bruker_transient'

    if ext == 'raw':
        return 'thermo_reduced_profile'

def check_ftms_parameters():

    if not current_user.ftms_parameters.first():

        ms_settings = MassSpectrumSetting()
        mspeak_settings = MassSpecPeakSetting()
        molformula_settings = MolecularFormulaSearchSettings()
        transient_settings = TransientSetting()

        # no parameters found in the database creating one
        # default kendrick
        # default usedAtoms
        molformula_settings.usedAtoms = {'C': (1, 100), 'H': (4, 200), 'O': (1, 22)}
        molformula_settings.used_atom_valences = {'C': 4,
                                                    '13C': 4,
                                                    'H': 1,
                                                    'O': 2,
                                                    '18O': 2,
                                                    'N': 3,
                                                    'S': 2,
                                                    '34S': 2,
                                                    'P': 3,
                                                    'Cl': 1,
                                                    '37Cl': 1,
                                                    'Br': 1,
                                                    'Na': 1,
                                                    'F': 1,
                                                    'K': 1
                                                  }

        basic_dict = {'ion_charge': molformula_settings.ion_charge,
                      'use_pah_line_rule': molformula_settings.use_pah_line_rule,
                      'min_dbe': molformula_settings.min_dbe,
                      'max_dbe': molformula_settings.max_dbe,
                      'isRadical': molformula_settings.isRadical,
                      'isProtonated': molformula_settings.isProtonated,
                      'isAdduct': molformula_settings.isAdduct,
                      'adduct_atoms_neg': molformula_settings.adduct_atoms_neg,
                      'adduct_atoms_pos': molformula_settings.adduct_atoms_pos,
                      'ionization_type': molformula_settings.ionization_type,
                      'min_ppm_error': molformula_settings.min_ppm_error,
                      'max_ppm_error': molformula_settings.max_ppm_error,
                      'usedAtoms': molformula_settings.usedAtoms,
                      'used_atom_valences': molformula_settings.used_atom_valences,
                      'url_database': molformula_settings.url_database,
                      'output_score_method': molformula_settings.output_score_method,
                      'output_min_score': molformula_settings.output_min_score
                      }

        advanced_dict = {'use_isotopologue_filter': molformula_settings.use_isotopologue_filter,
                         'isotopologue_filter_threshold': molformula_settings.isotopologue_filter_threshold,
                         'isotopologue_filter_atoms': molformula_settings.isotopologue_filter_atoms,
                         'use_runtime_kendrick_filter': molformula_settings.use_runtime_kendrick_filter,
                         'use_min_peaks_filter': molformula_settings.use_min_peaks_filter,
                         'min_peaks_per_class': molformula_settings.min_peaks_per_class,
                         'min_hc_filter': molformula_settings.min_hc_filter,
                         'max_hc_filter': molformula_settings.max_hc_filter,
                         'min_oc_filter': molformula_settings.min_oc_filter,
                         'max_oc_filter': molformula_settings.max_oc_filter,
                         'min_op_filter': molformula_settings.min_op_filter,
                         'score_method': molformula_settings.score_method,
                         'min_abun_error': molformula_settings.min_abun_error,
                         'max_abun_error': molformula_settings.max_abun_error,
                         'error_method': molformula_settings.error_method,
                         'mz_error_average': molformula_settings.mz_error_average,
                         }

        input_setting_dict = {'mz_label': 'm/z',
                                'abundance_label': 'I',
                                'sn_label': 'S/N',
                                'resolving_power_label': 'Res.'
                              }

        data = {'user_id': current_user.id,
                'name': 'default',
                'ms_peak_parameters': json.dumps(mspeak_settings.__dict__),
                'basic_parameters': json.dumps(basic_dict),
                'ms_parameters': json.dumps(ms_settings.__dict__),
                'transient_parameters': json.dumps(transient_settings.__dict__),
                'advanced_parameters': json.dumps(advanced_dict),
                'input_data_parameters': json.dumps(input_setting_dict)
                }

        ftms_parameters = FTMS_Parameters(**data)
        db.session.add(ftms_parameters)
        db.session.commit()
        return ftms_parameters

    else: return current_user.ftms_parameters.order_by(FTMS_Parameters.id.desc()).first()


def populate_ms_form(ftms_parameters=None):

    if not ftms_parameters:

        ftms_parameters = check_ftms_parameters()

    parameter_data = ftms_parameters.ms_parameters_dict

    form = MassSpectrumSettingForm(MultiDict(parameter_data))

    return form

def populate_input_settings_form(ftms_parameters=None):

    if not ftms_parameters:

        ftms_parameters = check_ftms_parameters()

    parameter_data = ftms_parameters.input_data_parameters_dict

    form = DataInputSettingForm(MultiDict(parameter_data))

    return form

def populate_transient_form(ftms_parameters=None):

    if not ftms_parameters:

        ftms_parameters = check_ftms_parameters()

    parameter_data = ftms_parameters.transient_parameters_dict

    form = TransientSettingForm(MultiDict(parameter_data))

    return form

def populate_advanced_form(ftms_parameters=None):

    if not ftms_parameters:

        ftms_parameters = check_ftms_parameters()

    parameter_data = ftms_parameters.advanced_parameters_dict

    form = AdvancedFtmsSettingsForm(MultiDict(parameter_data))

    return form

def populate_mspeak_form(ftms_parameters=None):

    if not ftms_parameters:

        ftms_parameters = check_ftms_parameters()

    # populate the form with the parameters found in the db
    # get the data_dictionary
    parameter_data = ftms_parameters.ms_peak_parameters_dict

    form = MassSpecPeakSettingForm(MultiDict(parameter_data))

    # populate form kendrick base
    kendrick_dict = parameter_data.get('kendrick_base')

    for atom, count in kendrick_dict.items():

        kendrick = KendrickForm()
        kendrick.atoms = atom
        kendrick.count = count

        form.kendrickAtoms.append_entry(kendrick)

    return form

def populate_basic_form(ftms_parameters=None):

    if not ftms_parameters:

        ftms_parameters = check_ftms_parameters()

    # get the data_dictionary
    parameter_data = ftms_parameters.basic_parameters_dict

    # populate the form with the parameters found in the db
    form = BasicFtmsSettingsForm(MultiDict(parameter_data))

    # populate form used atoms
    used_atoms_dict = parameter_data.get('usedAtoms')
    used_atoms_valence_dict = parameter_data.get('used_atom_valences')

    for atom, min_max in used_atoms_dict.items():

        usedAtoms = UsedAtom()
        usedAtoms.atom = atom
        usedAtoms.min_count = min_max[0]
        usedAtoms.max_count = min_max[1]
        usedAtoms.atoms_valence = used_atoms_valence_dict.get(atom)
        form.usedAtoms.append_entry(usedAtoms)

    return form

def basic_form_to_dict(basic_form, clean_data):

    usedAtoms = {}
    used_atom_valences = {}

    for data in basic_form.usedAtoms.data:
        usedAtoms[data.get('atom')] = (int(data.get('min_count')), int(data.get('max_count')))
        used_atom_valences[data.get('atom')] = int(data.get('atoms_valence'))
        # print(results)

    clean_data['output_score_method'] = basic_form.data.get('output_score_method')
    #clean_data['output_min_score'] = basic_form.data.get('output_min_score')
    clean_data['usedAtoms'] = usedAtoms
    clean_data['used_atom_valences'] = used_atom_valences
    clean_data['isProtonated'] = basic_form.data.get('isProtonated')
    clean_data['isRadical'] = basic_form.data.get('isRadical')
    clean_data['isAdduct'] = basic_form.data.get('isAdduct')
    clean_data['use_pah_line_rule'] = basic_form.data.get('use_pah_line_rule')
    

    return clean_data

def advanced_form_to_dict(advanced_form, clean_data):

    clean_data['use_isotopologue_filter'] = advanced_form.data.get('use_isotopologue_filter')
    clean_data['use_runtime_kendrick_filter'] = advanced_form.data.get('use_runtime_kendrick_filter')
    clean_data['use_min_peaks_filter'] = advanced_form.data.get('use_min_peaks_filter')

    return clean_data

def input_settings_form_to_dict(advanced_form, clean_data):

    clean_data['use_isotopologue_filter'] = advanced_form.data.get('use_isotopologue_filter')
    clean_data['use_runtime_kendrick_filter'] = advanced_form.data.get('use_runtime_kendrick_filter')
    clean_data['use_min_peaks_filter'] = advanced_form.data.get('use_min_peaks_filter')

    return clean_data

def mspeak_form_to_dict(ms_peak_form, clean_data):

    kendrick_base = {}

    for data in ms_peak_form.kendrickAtoms.data:
        kendrick_base[data.get('atoms')] = int(data.get('count'))

        # print(results)
        clean_data['kendrick_base'] = kendrick_base

    return clean_data

def clean_dict(data):

    return {key: value[0] if len(value) == 1 else value
                            for key, value in data.items()
                            if 'submit' not in key and
                            'usedAtoms-' not in key and
                            'csrf_token' not in key and
                            'kendrickAtoms-' not in key
            }

def clean_form(form):

    return {key: value[0] if len(value) == 1 else value
                            for key, value in form.lists()
                            if 'submit' not in key and
                            'usedAtoms-' not in key and
                            'csrf_token' not in key and
                            'kendrickAtoms-' not in key
            }
