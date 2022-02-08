
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, BooleanField, SubmitField, SelectField, IntegerField, DecimalField, SelectMultipleField
from wtforms import FieldList, FileField, Form, FormField, MultipleFileField, RadioField, validators, widgets, TextField
from wtforms.fields.html5 import EmailField, IntegerRangeField
from wtforms.validators import DataRequired, Email
from app.models.ftms_model import FTMS_Data, FTMS_Parameters, FTMS_Result
from corems.encapsulation.constant import Atoms
from flask_wtf.file import FileAllowed

#ATOMS_CHOICES = [('C', 'C'), ('H', 'H'), ('N', 'N'), ('S', 'S'), ('O', 'O'), ('P', 'P'), ('Cl', 'Cl')]

ATOMS_CHOICES = [(key, key) for key in Atoms.atomic_masses.keys()]

class MultiRadioField(SelectMultipleField):
    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class KendrickForm(FlaskForm):
    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    atoms = SelectField('Atom Label: ', choices=ATOMS_CHOICES)
    count = IntegerField('Atom Count: ')

class UsedAtom(FlaskForm):
    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    atom = SelectField('Atom Label: ', choices=ATOMS_CHOICES)
    min_count = IntegerField('Min Count: ')
    max_count = IntegerField('Max Count: ')
    atoms_valence = IntegerField('Covalence: ')

class ParametersPresetsForm(FlaskForm):

    add_preset = SubmitField('Save Current Settings')

    ftms_presets = SelectField('Load Settings')

    new_preset_name = StringField('Save Current Settings :', [validators.required()])

    def __init__(self):

        super(ParametersPresetsForm, self).__init__()

        all_ftms_parameter = current_user.ftms_parameters.order_by(FTMS_Parameters.id.desc()).all()

        self.ftms_presets.choices = [(str(c.id), c.name) for c in all_ftms_parameter]


class FTMSSubmitJob(FlaskForm):

    data_to_process = SelectMultipleField('Select Files', [validators.required()])
    reference_file = SelectField('Select Calibration Reference File', [validators.required()])
    submit = SubmitField('Submit Job')

    def __init__(self):

        super(FTMSSubmitJob, self).__init__()

        all_ftms_data = current_user.ftms_data.order_by(FTMS_Data.id.desc()).all()

        self.data_to_process.choices = [(str(c.id), "{}{}".format(c.name, c.modifier)) for c in all_ftms_data if c.suffix != '.ref']
        self.reference_file.choices = [(str(c.id), "{}{}".format(c.name, c.modifier)) for c in all_ftms_data if c.suffix == '.ref']
        self.reference_file.choices.append((str(0), 'None/Do Not Recalibrate'))


class FtmsFileInputForm(FlaskForm):

    cal_ref_file = MultipleFileField('Calibration Reference File (.ref)', validators=[
        FileAllowed(['ref'])
    ])

    files = MultipleFileField('Thermo Raw Files (.txt, .raw)', validators=[
        FileAllowed(['raw'])
    ])

    centroid_file = MultipleFileField('Mass List Centroid (.csv, .txt, .pks)', validators=[
        FileAllowed(['txt', 'csv', 'pks'])
    ])
    
    profile_file = MultipleFileField('Mass List Profile (.csv, .txt)', validators=[
        FileAllowed(['txt', 'csv'])
    ])

    bruker_files = FileField('Bruker Raw File (.d ) Use only with Chrome or Firefox Browsers')
    outfilename = StringField('Dataset name')
    submit = SubmitField('Upload Data')

class TransientSettingForm(FlaskForm):
    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    submittransient = SubmitField('Update Parameters')

    apodization_method = SelectField('Apodization Method: ', choices=[('Hamming', 'Hamming'),
                                                                      ('Hanning', 'Hanning'),
                                                                      ('Blackman', 'Blackman')],
                                                             default='Hamming')

    number_of_truncations = IntegerField('Transient Truncations', default=0)
    number_of_zero_fills = IntegerField('Transient ZeroFills', default=1)


class MassSpectrumSettingForm(FlaskForm):
    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    submitms = SubmitField('Update Parameters')

    threshold_method = SelectField('Noise Threshold: ', choices=[('auto', 'auto'),
                                                                 ('signal_noise', 'signal/noise'),
                                                                 ('relative_abundance', 'relative abundance')],
                                                        default='auto')

    noise_threshold_std = IntegerField('Auto Noise Threshold (std)', default=6)

    s2n_threshold = DecimalField('Signal/Noise Threshold: ', default=4.00)

    relative_abundance_threshold = DecimalField('Relative Abundance Threshold: ', default=6.00)

    min_noise_mz = DecimalField('Min m/z auto noise: ', places=5, default=100.00000)
    max_noise_mz = DecimalField('Max m/z auto noise: ', places=5, default=1200.00000)

    min_picking_mz = DecimalField('Min m/z: ', places=5, default=100.00000)
    max_picking_mz = DecimalField('Max m/z: ', places=5, default=1200.00000)

    start_scan = IntegerField('Start', default=1)
    final_scan = IntegerField('End', default=7)

    calib_minimize_method = SelectField('Calibration Optimization Method: ', choices=[('Powell', 'Powell')], default='Powell')
    calib_pol_order = IntegerField('Calibration Optimization Polynomial Order: ', default=2)
    calib_sn_threshold = DecimalField('Calibration S/N Threshold: ', default=10.00)

    min_calib_ppm_error = DecimalField('Min Calibration error (ppm): ', places=5, default=-1.00000)
    max_calib_ppm_error = DecimalField('Max Calibration error (ppm): ', places=5, default=1.00000)

class DataInputSettingForm(FlaskForm):
    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    submitdatainput = SubmitField('Update Parameters')
    # kendrick_base : Dict =  {'C': 1, 'H':2}
    mz_label = TextField("m/z", default='m/z')
    abundance_label = TextField("Peak Height", default='I')
    sn_label = TextField("S/N", default='S/N')
    resolving_power_label = TextField("Resolving Power", default='Res.')


class MassSpecPeakSettingForm(FlaskForm):
    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    submitpeak = SubmitField('Update Parameters')
    # kendrick_base : Dict =  {'C': 1, 'H':2}
    kendrickAtoms = FieldList(FormField(KendrickForm), min_entries=0, max_entries=10)

    peak_min_prominence_percent = DecimalField('Min Peak Prominence (%): ', default=1.00)
    peak_max_prominence_percent = DecimalField('Max Peak Prominence (%): ', default=0.10)

    # return self

class BasicFtmsSettingsForm(FlaskForm):

    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    submitBasic = SubmitField('Update Parameters')

    ion_charge = RadioField('Polarity: ', choices=[("-1", -1), ("1", 1)], default="-1")

    use_pah_line_rule = BooleanField('PAH Line Filter: ', default=False)

    min_dbe = DecimalField('Min DBE: ', default=0.0)

    max_dbe = DecimalField('Max DBE: ', default=40.0)

    isRadical = BooleanField('Radical  ', default=False)

    isProtonated = BooleanField('Protonated  ', default="checked")

    isAdduct = BooleanField('Adduct  ', default=False)

    adduct_atoms_neg = MultiRadioField('Search Adducts Atoms Neg: ', choices=[('Cl', 'Cl'), ('Br', 'Br')])

    adduct_atoms_pos = MultiRadioField('Search Adducts Atoms Pos: ', choices=[('Na', 'Na'), ('K', 'K')])

    ''' search setting '''
    ionization_type = RadioField('Ionization Technique: ', choices=[('esi', 'ESI'),
                                                                    ('appi', 'APPI'),
                                                                    ('apci', 'APCI')], default='esi')

    # empirically set / needs optimization
    min_ppm_error = DecimalField('Min Search Error (ppm): ', places=5, default=-1.00000)
    max_ppm_error = DecimalField('Max Search Error (ppm): ', places=5, default=1.00000)

    usedAtoms = FieldList(FormField(UsedAtom), min_entries=0, max_entries=100)

    output_score_method = SelectField('Confidence Score: ', choices=[('prob_score', 'Highest Assigment Score'),
                                                                     ('lowest_error', 'Lowest Error'),
                                                                     ('S_P_lowest_error', 'S P and lowest_error'),
                                                                     ('N_S_P_lowest_error', 'N S P lowest_error'),
                                                                     ('None', 'Assigment Score Filter')],
                                                                     default='Assigment Score Filter')

    output_min_score = DecimalField('Export Min Score: ', places=0.4, default=-0.1)                          

class AdvancedFtmsSettingsForm(FlaskForm):
    class Meta:
        """Subform.
        CSRF is disabled for this subform (using `Form` as parent class) because
        """
        csrf = False

    submitAdvanced = SubmitField('Update Parameters')

    use_isotopologue_filter = BooleanField('Isotopologue Filter: ')

    isotopologue_filter_threshold = DecimalField('Min Rate(%): ', default=33.00)

    isotopologue_filter_atoms = MultiRadioField('Atoms: ', choices=[('Cl', 'Cl'), ('Br', 'Br')])

    use_runtime_kendrick_filter = BooleanField('Kendrick Cluster Filter: ', default=False, false_values={False, 'false', ''})

    use_min_peaks_filter = BooleanField('Min Assigned Mol. Formula per Class: ', default=False, false_values={False, 'false', ''})

    min_peaks_per_class = IntegerField('Min Mol. Formula per Class: ', default=1.00)

    # url_database: str = 'postgresql://coremsdb:coremsmolform@localhost:5432/molformula'
    # db_jobs: int = 3

    '''query setting'''

    min_hc_filter = DecimalField('Min H/C Filter: ', default=0.3)
    max_hc_filter = DecimalField('Max H/C Filter: ', default=3.0)

    min_oc_filter = DecimalField('Min O/C Filter: ', default=0.0)
    max_oc_filter = DecimalField('Max O/C Filter: ', default=1.2)

    min_op_filter = DecimalField('Min O/P Filter: ', default=2.0)

    '''assignemt setting'''
    # look for close shell ions [M + Adduct]+ only considers metal set in the list adduct_atoms

    score_method = SelectField('Confidence Score Method: ', choices=[('prob_score', 'Probability Score'),
                                                              ('lowest_error', 'Lowest Error'),
                                                              ('S_P_lowest_error', 'S P and lowest_error'),
                                                              ('N_S_P_lowest_error', 'N S P lowest_error'),
                                                              ('None', 'All Candidates')],
                                                            default='All Candidates')

    # empirically set / needs optimization set for isotopologue search
    min_abun_error = DecimalField('Min Abundance Error (%): ', places=2, default=-100)
    max_abun_error = DecimalField('Max Abundance Error (%): ', places=2, default=100)

    # 'distance', 'lowest', 'symmetrical','average' 'None'
    error_method = SelectField('Error Search Method: : ', choices=[('None', 'None'),
                                                                   ('distance', 'Distance'),
                                                                   ('lowest', 'Lowest'),
                                                                   ('symmetrical', 'Symmetrical'),
                                                                   ('average', 'Average')], default='None')
    
    # empirically set / needs optimization
    mz_error_range = DecimalField('Error Search Limit (ppm): ', places=5, default=1.5)
    mz_error_average = DecimalField('Start Error Average (ppm): ', places=5, default=0.0)

    # used_atom_valences: {'C': 4, 'H':1, etc} = field(default_factory=dict)

    '''
    usedAtoms = {'C': (1, 100),
                 'H': (4, 200),
                 'O': (1, 22),
                 'N': (0, 0),
                 'S': (0, 0),
                 'P': (0, 0),
                 'Cl': (0, 0),
                 }

    used_atom_valences = {'C': 4,
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
    '''
