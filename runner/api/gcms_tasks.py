from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path
import json

from corems.mass_spectra.input.andiNetCDF import ReadAndiNetCDF
from corems.encapsulation.input import parameter_from_json
from corems.mass_spectra.calc.GC_RI_Calibration import get_rt_ri_pairs
from corems.molecular_id.search.compoundSearch import LowResMassSpectralMatch
from corems.encapsulation.factory.processingSetting import CompoundSearchSettings, GasChromatographSetting
from corems.encapsulation.factory.parameters import GCMSParameters


from api.celery import app
from api.models.auth import User
from api.models.gcms import GCMS_Result
from api.sqlalchemy import session
from api import config as Config
from s3path import S3Path

def query_parameters(current_user, parameters_id) -> GCMSParameters:

    gcms_parameters = current_user.gcms_parameters.filter_by(id = parameters_id).first()

    basic_dict = gcms_parameters.basic_parameters_dict
    advanced_dict = gcms_parameters.advanced_parameters_dict

    molecular_search = CompoundSearchSettings(**basic_dict)
    gc_ms = GasChromatographSetting(**advanced_dict)

    # TODO add spectral lib address
    molecular_search.url_database = Config.SPECTRAL_GCMS_DATABASE_URL

    parameter_class = GCMSParameters()
    parameter_class.molecular_search = molecular_search
    parameter_class.gc_ms = gc_ms

    return parameter_class

def run_workflow(current_user, file_class, gcms_results, cal_file_class, parameters_id):

    parameters = query_parameters(current_user, parameters_id)

    cal_file_path = cal_file_class.filepath

    cal_s3path = S3Path('/gcms-data/' + cal_file_path)

    file_path = file_class.filepath

    s3path = S3Path('/gcms-data/' + file_path)

    rt_ri_pairs = get_calibration_rtri_pairs(cal_s3path, parameters)

    gcms = get_gcms(s3path, parameters)

    gcms.calibrate_ri(rt_ri_pairs, cal_s3path)

    # sql_obj = start_sql_from_file()
    # lowResSearch = LowResMassSpectralMatch(gcms, sql_obj=sql_obj)
    # !!!!!! READ !!!!! use the previous two lines if
    # db/pnnl_lowres_gcms_compounds.sqlite does not exist
    # and comment the next line
    lowResSearch = LowResMassSpectralMatch(gcms)
    lowResSearch.run()

    gcms_results_id = add_gcms_results_db(gcms_results, gcms, parameters.gc_ms.use_deconvolution)

    return gcms_results_id

def get_calibration_rtri_pairs(file_path, gcms_paramaters_class):

    gcms_ref_obj = get_gcms(file_path, gcms_paramaters_class)
    # sql_obj = start_sql_from_file()
    # rt_ri_pairs = get_rt_ri_pairs(gcms_ref_obj,sql_obj=sql_obj)
    # !!!!!! READ !!!!! use the previous two lines if db/pnnl_lowres_gcms_compounds.sqlite does not exist
    # and comment the next line
    rt_ri_pairs = get_rt_ri_pairs(gcms_ref_obj)

    return rt_ri_pairs

def get_gcms(file_path, parameter_class):

    reader_gcms = ReadAndiNetCDF(file_path)

    reader_gcms.run()

    gcms = reader_gcms.get_gcms_obj()

    # parameter_from_json.load_and_set_parameters_gcms(gcms, parameters_path=corems_params)
    gcms.parameter = parameter_class

    gcms.process_chromatogram()

    return gcms

@app.task(bind=True)
def run_gcms_metabolomics_workflow(self, args):

    current_user_id, file_id, cal_file_id, parameters_id, gcms_result_id = args

    current_user, file_class, cal_file_class, gcms_results = update_gcms_result(current_user_id, file_id, cal_file_id, gcms_result_id)

    try:

        run_workflow(current_user, file_class, gcms_results, cal_file_class, parameters_id)
        # TODO save stats
        return {'current': 100, 'total': 100, 'status': 'Task completed!',
                'result': 'OK'}

    except Exception as exception:
        # TODO save exception

        gcms_results.status = 'Fail'
        gcms_results.stats = json.dumps({'error': str(exception)}, sort_keys=False, indent=4, separators=(',', ': '))

        session.commit()

        return {'current': 100, 'total': 100, 'status': 'Task completed!',
                'result': str(exception)}

def update_gcms_result(user_id, file_id, cal_file_id, gcms_result_id):

    current_user = User.query.get(user_id)

    # release session
    session.commit()

    # get class objs
    file_class = current_user.gcms_data.filter_by(id = file_id).first()
    cal_file_class = current_user.gcms_data.filter_by(id = cal_file_id).first()

    gcms_results = current_user.gcms_results.filter_by(id = gcms_result_id).first()
    gcms_results.status = 'Active'
    gcms_results.data_id = file_id
    session.commit()

    return current_user, file_class, cal_file_class, gcms_results

def add_gcms_results_db(gcms_results, gcms, use_deconvolution):

    # i, j, total_percent, total_relative_abundance, rms_error = mass_spec.percentile_assigned(report_error=True)
    # stats = '%i peaks assigned and %i peaks not assigned, total  = %.2f %%, relative abundance = %.2f %%, RMS error (best candidate) (ppm) = %.3f' % (i, j, total_percent, total_relative_abundance, rms_error)
    # stats = {'assigned': i,
    #         'unassigned': j,
    #         'perc_abundance': total_relative_abundance,
    #         'rms': rms_error}

    gcms_results.data_table = gcms.to_json()
    gcms_results.parameters = gcms.parameters_json()

    gcms_results.peaks = gcms.peaks_rt_tic(json_string=True)

    gcms_results.rt = gcms.retention_time
    gcms_results.tic = gcms.tic
    gcms_results.stats = json.dumps(gcms.processing_stats())
    gcms_results.status = 'Success'
    session.commit()
