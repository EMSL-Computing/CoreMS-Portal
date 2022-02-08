
from pathlib import Path

from corems.mass_spectrum.calc.Calibration import MzDomainCalibration
from corems.mass_spectrum.input.massList import ReadMassList
from corems.molecular_id.search.molecularFormulaSearch import SearchMolecularFormulas
from corems.transient.input.brukerSolarix import ReadBrukerSolarix
from corems.encapsulation.factory.parameters import MSParameters
from corems.encapsulation.factory.processingSetting import MassSpecPeakSetting, MassSpectrumSetting, \
                                                    MolecularFormulaSearchSettings, TransientSetting, \
                                                    LiqChromatographSetting, DataInputSetting

from api.celery import app
from api.models.auth import User
from api.models.ftms import FTMS_Result
from api.sqlalchemy import session
from api import config as Config
import json
from s3path import S3Path

def query_parameters(current_user, parameters_id) -> MSParameters:

    ftms_parameters = current_user.ftms_parameters.filter_by(id=parameters_id).first()

    basic_dict = ftms_parameters.basic_parameters_dict
    advanced_dict = ftms_parameters.advanced_parameters_dict
    ms_parameters = ftms_parameters.ms_parameters_dict
    ms_peak_parameters = ftms_parameters.ms_peak_parameters_dict
    transient_parameters = ftms_parameters.transient_parameters_dict
    data_input_parameters = ftms_parameters.input_data_parameters_dict

    data_input_settings = DataInputSetting()
    data_input_settings.add_mz_label(data_input_parameters.get('mz_label'))
    data_input_settings.add_peak_height_label('abundance_label')
    data_input_settings.add_sn_label('sn_label')
    data_input_settings.add_resolving_power_label('resolving_power_label')

    lc_settings = LiqChromatographSetting()
    lc_settings.start_scan = int(ms_parameters.pop('start_scan', 1))
    lc_settings.final_scan = int(ms_parameters.pop('final_scan', 1))

    ms_settings = MassSpectrumSetting(**ms_parameters)
    mspeak_settings = MassSpecPeakSetting(**ms_peak_parameters)
    molformula_settings = MolecularFormulaSearchSettings(**{**basic_dict, **advanced_dict})
    transient_settings = TransientSetting(**transient_parameters)
    molformula_settings.url_database = Config.COREMS_DATABASE_URL

    molformula_settings.mz_error_score_weight = 0.7
    molformula_settings.isotopologue_score_weight = 0.3

    parameter_class = MSParameters()
    parameter_class.mass_spectrum = ms_settings
    parameter_class.ms_peak = mspeak_settings
    parameter_class.molecular_search = molformula_settings
    parameter_class.transient = transient_settings
    parameter_class.lc = lc_settings
    parameter_class.data_input = data_input_settings

    return parameter_class

def run_workflow(current_user, file_location, filetype, ref_calibration_file, parameters_id):

    parameters = query_parameters(current_user, parameters_id)

    first_scan = parameters.lc.start_scan
    last_scan = parameters.lc.final_scan

    if filetype == 'thermo_reduced_profile':

        from corems.mass_spectra.input import rawFileReader

        reader = rawFileReader.ImportMassSpectraThermoMSFileReader(file_location)
        # auto_process set to false to allow noise and peak picking settings to be updated later
        mass_spectrum = reader.get_average_mass_spectrum_in_scan_range(first_scan, last_scan, auto_process=False)

    elif filetype == 'bruker_transient':

        with ReadBrukerSolarix(file_location) as transient:
            # auto_process set to false to allow noise and peak picking settings to be updated later
            transient.parameters = parameters.transient
            mass_spectrum = transient.get_mass_spectrum(plot_result=False, auto_process=False)

    elif filetype == 'centroid_masslist':

        reader = ReadMassList(file_location)

        reader.parameters = parameters.data_input
        mass_spectrum = reader.get_mass_spectrum(parameters.molecular_search.ion_charge)

    elif filetype == 'profile_masslist':

        reader = ReadMassList(file_location, header_lines=7, isCentroid=False, isThermoProfile=True)

        reader.parameters = parameters.data_input
        mass_spectrum = reader.get_mass_spectrum(parameters.molecular_search.ion_charge)
    else:

        raise Exception("Filetype: {} not supported".format(filetype))

    # store setting inside mass spectrum obj
    mass_spectrum.parameters = parameters

    if mass_spectrum.is_centroid:

        mass_spectrum.filter_by_noise_threshold()

    else:
        # process the mass spectrum after the settings are updated
        mass_spectrum.process_mass_spec()
    # force it to one job. daemon child can not have child process
    mass_spectrum.molecular_search_settings.db_jobs = 1

    if ref_calibration_file:

        MzDomainCalibration(mass_spectrum, ref_calibration_file).run()

    SearchMolecularFormulas(mass_spectrum, first_hit=False).run_worker_mass_spectrum()

    return mass_spectrum

def workflow_worker(current_user, file_class, ftmsresults, id_cal_file, parameters_id):

    reference_class = current_user.ftms_data.filter_by(id = id_cal_file).first()

    filepath = file_class.filepath

    filetype = file_class.filetype

    s3path = S3Path('/fticr-data/' + filepath)

    ref_calibration_file = reference_class.filepath if reference_class else None

    s3path_ref_calibration_file = S3Path('/fticr-data/' + ref_calibration_file) if ref_calibration_file else None

    mass_spec = run_workflow(current_user, s3path, filetype, s3path_ref_calibration_file, parameters_id)

    # dirloc = Path(workflow_params.output_directory) / workflow_params.output_group_name / mass_spec.sample_name

    # dirloc.mkdir(exist_ok=True, parents=True)

    # output_path = dirloc / mass_spec.sample_name

    # eval('mass_spec.to_{OUT_TYPE}(output_path)'.format(OUT_TYPE=workflow_params.output_type))
    ftmsresults_id = add_ftms_results_db(ftmsresults, mass_spec)

    return ftmsresults_id

def add_ftms_results_db(ftmsresults, mass_spec):

    i, j, total_percent, total_relative_abundance, rms_error = mass_spec.percentile_assigned(report_error=True)
    stats = '%i peaks assigned and %i peaks not assigned, total  = %.2f %%, relative abundance = %.2f %%, RMS error (best candidate) (ppm) = %.3f' % (i, j, total_percent, total_relative_abundance, rms_error)
    stats = {'assigned': i,
             'unassigned': j,
             'perc_abundance': total_relative_abundance,
             'rms': rms_error}

    ftmsresults.data_table = mass_spec.to_json()
    ftmsresults.parameters = mass_spec.parameters_json()
    ftmsresults.mz_raw = mass_spec.mz_exp_profile
    ftmsresults.abun_raw = mass_spec.abundance_profile
    ftmsresults.stats = json.dumps(stats)
    ftmsresults.status = 'Success'

    session.commit()

def update_ftms_result(user_id, file_id, ftmsresult_id):

    current_user = User.query.get(user_id)

    # release session
    session.commit()

    # get class objs
    file_class = current_user.ftms_data.filter_by(id = file_id).first()

    ftmsresults = current_user.ftms_results.filter_by(id = ftmsresult_id).first()
    ftmsresults.status = 'Active'
    session.commit()

    return current_user, file_class, ftmsresults

@app.task(bind=True)
def run_srfa_qc_workflow(self, args):

    current_user_id, file_id, id_cal_file, parameters_id, ftmsresult_id = args

    current_user, file_class, ftmsresults = update_ftms_result(current_user_id, file_id, ftmsresult_id)

    try:

        workflow_worker(current_user, file_class, ftmsresults, id_cal_file, parameters_id)
        # TODO save stats
        return {'current': 100, 'total': 100, 'status': 'Task completed!',
                'result': 'OK'}

    except Exception as exception:
        # TODO save exception

        ftmsresults.status = 'Fail'
        ftmsresults.stats = json.dumps({'error': str(exception)}, sort_keys=False, indent=4, separators=(',', ': '))

        session.commit()

        return {'current': 100, 'total': 100, 'status': 'Task Failed!',
                'result': str(exception)}
