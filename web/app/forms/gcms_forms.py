
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import FileField, MultipleFileField, SubmitField, SelectMultipleField, \
                    SelectField, StringField, DecimalField, IntegerField, BooleanField
from wtforms import validators
from flask_wtf.file import FileAllowed
from app.models.gcms_model import GCMS_Data, GCMS_Parameters

ri_calibration_compound_names = (" [C8] Methyl Caprylate [7.812]",
                                 " [C10] Methyl Caprate [10.647]",
                                 " [C9] Methyl Pelargonate [9.248]",
                                 " [C12] Methyl Laurate [13.250]",
                                 " [C14] Methyl Myristate [15.597]",
                                 " [C16] Methyl Palmitate [17.723]",
                                 " [C18] Methyl Stearate [19.663]",
                                 " [C20] Methyl Eicosanoate [21.441]",
                                 " [C22] Methyl Docosanoate [23.082]",
                                 " [C24] Methyl Linocerate [24.603]",
                                 " [C26] Methyl Hexacosanoate [26.023]",
                                 " [C28] Methyl Octacosanoate [27.349]",
                                 " [C30] Methyl Triacontanoate [28.72]")

class GcmsFileInputForm(FlaskForm):

    gcms_cal_ref_file = FileField('Calibration Reference File (.cdf)', validators=[
                                                                  FileAllowed(['cdf'])])

    gcms_blank_file = FileField('Blank Data File (.cdf)', validators=[
                                                FileAllowed(['cdf'])])

    gcms_files = MultipleFileField('Sample Data Files (.cdf)', validators=[
                                                        FileAllowed(['cdf'])])
    gcms_upload_submit = SubmitField('Upload Data')

class GcmsSubmitJob(FlaskForm):

    gcms_data_to_process = SelectMultipleField('Select Files', [validators.required()])
    gcms_reference_file = SelectField('Select Calibration Reference File', [validators.required()])
    gcms_submit = SubmitField('Submit Job')

    def __init__(self, *args, **kargs):

        super(GcmsSubmitJob, self).__init__(*args, **kargs)

        all_gcms_data = current_user.gcms_data.order_by(GCMS_Data.id.desc()).all()

        self.gcms_data_to_process.choices = [(str(c.id), "{}{}".format(c.name, c.modifier)) for c in all_gcms_data if not c.is_calibration]
        self.gcms_reference_file.choices = [(str(c.id), "{}{}".format(c.name, c.modifier)) for c in all_gcms_data if c.is_calibration]
        self.gcms_reference_file.choices.append((str(0), 'None'))

class GcmsParametersPresetsForm(FlaskForm):

    add_gcms_preset = SubmitField('Save Current Settings')

    gcms_presets = SelectField('Load Settings')

    new_gcms_preset_name = StringField('Save Current Settings :', [validators.required()])

    def __init__(self, *args, **kargs):

        super(GcmsParametersPresetsForm, self).__init__(*args, **kargs)

        all_gcms_parameter = current_user.gcms_parameters.order_by(GCMS_Parameters.id.desc()).all()

        self.gcms_presets.choices = [(str(c.id), c.name) for c in all_gcms_parameter]

class CompoundSearchSettingsForm(FlaskForm):

    submitcompoundsearch = SubmitField('Update Parameters')

    ri_search_range = DecimalField('RI Search Range', default=20.0)

    rt_search_range = DecimalField('RT Search Range', default=1.0)

    correlation_threshold = DecimalField('Spectral Similarity Threshold', default=0.5)

    score_threshold = DecimalField('Similarity Score Threshold', default=0.0)

    output_score_method = SelectField('Confidence Score: ', choices=[('highest_sim_score', 'Highest Score'),
                                                                     ('highest_ss', 'Highest Spectral Similarity'),
                                                                     ('None', 'All Candidates')],
                                                                     default='All Candidates')

    ri_std = DecimalField('RI Std (Similarity Score)', default=3.0)

    ri_calibration_compound_names = SelectMultipleField('Select R.I. Reference Compounds')

    exploratory_mode = BooleanField('Calculate All Spectral Similarities',  default=0)

    def __init__(self, *args, **kargs):

        super(CompoundSearchSettingsForm, self).__init__(*args, **kargs)

        # all_ftms_data = current_user.ftms_data.order_by(FTMS_Data.time_stamp.desc()).all()
        self.ri_calibration_compound_names.choices = [(c, c) for c in ri_calibration_compound_names]


class GasChromatographSettingForm(FlaskForm):

    submitchromasettings = SubmitField('Update Parameters')

    use_deconvolution = BooleanField('Use m/z based deconvolution',  default=1)

    smooth_window = IntegerField('Smooth Window', default=5)

    smooth_method = SelectField('Smooth Method', choices=[('savgol', 'savgol'),
                                                                    ('hanning', 'hanning'),
                                                                    ('blackman', 'Blackman'),
                                                                    ('bartlett', 'Bartlett'),
                                                                    ('flat', 'Flat'),
                                                                    ('boxcar', 'boxcar')])

    peak_height_max_percent = DecimalField('Max Peak Height (%)', default=10.0) #1-100 % used for baseline detection use 0.1 for second_derivative and 10 for other methods

    peak_max_prominence_percent = DecimalField('Max Peak Prominence (%)', default=1.0) #1-100 % used for baseline detection

    min_peak_datapoints = DecimalField('Min Datapoint', default=5.0)

    max_peak_width = DecimalField('Max Peak Width (min)', default=0.1)

    noise_threshold_method = SelectField('Noise Threshold Method', choices=[('manual_relative_abundance', 'manual_relative_abundance'),
                                                                    ('auto_relative_abundance', 'auto_relative_abundance'),
                                                                    ('second_derivative', 'second_derivative')])

    std_noise_threshold = IntegerField('Std Noise Threshold (Auto Mode)', default=3)

    peak_height_min_percent = DecimalField('Min Peak Height (%)', default=0.1)  #0-100 % used for peak detection

    peak_min_prominence_percent = DecimalField('Min Peak Prominence (%)', default=0.1)  # 0-100 % used for peak detection

    eic_signal_threshold = DecimalField('Min EIC Peak Height (%)', default=0.01)  # 0-100 % used for extracted ion chromatogram peak detection

    max_rt_distance = DecimalField('Hierarchical Cluster Max Distance', default=0.025)  # minutes, max distance allowance hierarchical clutter
