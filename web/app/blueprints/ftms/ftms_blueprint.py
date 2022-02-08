from math import nan
from os import access
from pathlib import Path
import json
from datetime import datetime

import pytz


from app.models.auth_models import User
from bokeh.embed import components
from bokeh.resources import INLINE
from flask import flash, request, redirect, render_template, after_this_request, url_for
from flask import Blueprint, send_from_directory, Response
from flask import current_app, make_response, jsonify
from flask_login import login_required, current_user
from pandas import DataFrame
import requests
from s3path import S3Path
from werkzeug.utils import secure_filename

from app import db, minio, s3
from app.blueprints.ftms.ftms_forms import advanced_form_to_dict, allowed_file, basic_form_to_dict,\
                                           clean_dict, clean_form, mspeak_form_to_dict, populate_advanced_form,\
                                           populate_basic_form, populate_ms_form, populate_mspeak_form,\
                                           populate_transient_form, populate_input_settings_form

from app.forms.fticr_forms import AdvancedFtmsSettingsForm, BasicFtmsSettingsForm, FTMSSubmitJob, \
                                  FtmsFileInputForm, KendrickForm, MassSpecPeakSettingForm, \
                                  MassSpectrumSettingForm, ParametersPresetsForm, TransientSettingForm, \
                                  DataInputSettingForm

from app.models.ftms_model import FTMS_Data, FTMS_Parameters, FTMS_Result, FTMS_DataAccessLink
from app.models.auth_models import AccessGroup
from app.workflows.fticr.fticrms_workflow import generate_ftms_plots, run_direct_infusion_workflow
from app.workflows.fticr.ftms_open_data import run_load_data

from werkzeug.datastructures import MultiDict

fticrms = Blueprint('fticrms', __name__)
@fticrms.route('/ftms/instrument/start', methods=['GET', 'POST'])
@login_required
def test_local_api():
    # need to check if user has operator admin status
    # data will come from form
    token = current_user.encode_auth_token()
    corems_url = current_app.config['INSTRUMENT_API_URL']
    # corems_url = "http://localhost:3443"
    api_url = "/api/instrument/test"
    headers = {'x-access-tokens': token,
                   'Content-Type': 'application/json'}

    r = requests.get(url=corems_url + api_url, headers=headers)

    if r.status_code == 200:

        response_obj = {'status': 'success',
                        'message': 'All connections seems to be working fine',
                        'url': corems_url + api_url,
                        'text': r.text,
                         'token': token
                        }

        return response_obj, 200

    else:

        return r.json(), 500


@fticrms.route('/ftms/instrument/stop', methods=['POST'])
@login_required
def stop_scan_instrument():
    # need to check if user has operator admin status
    # data will come from form
    data = {"id": 1, "name": "12T_FTICRMS", "state": "scanning"}

    instrument_id = data["instrument_id"]

    # update state
    corems_url = "https://api.corem.emsl.pnl.gov"
    api_url = "/instrument/data/{}".format(instrument_id)
    headers = {'x-access-tokens': current_user.encode_auth_token(),
                   'Content-Type': 'application/json'}

    r = requests.put(url=corems_url + api_url, data=data, headers=headers)

    if r.status_code == 200:

        response_obj = {'status': 'success',
                        'message': 'Instrument {} flaged to stop scaning'.format(data['name'])
                        }

        return response_obj

    else:
        response_obj = {'status': 'fail',
                        'message': 'Instrument {} was not flaged to stop scaning'.format(instrument_id)
                        }
        return response_obj, 500

@fticrms.route('/ftms/results/<id>', methods=['GET'])
@login_required
def ftms_results(id):

    ftmsresults = current_user.ftms_results.filter(FTMS_Result.id == id).first()

    if ftmsresults:

        tab_widget = generate_ftms_plots(ftmsresults)

        js_resources = INLINE.render_js()
        # css_resources = INLINE.render_css()
        scripts_divs = list()

        scripts_divs.append(components(tab_widget))

        down_href = url_for('fticrms.download_table', id=id)
        html = render_template(
            'workflows/fticr/ftms_plots.html',
            script_list=scripts_divs,
            js_resources=js_resources,
            down_href=down_href)

        return html
    else:
        return redirect(url_for('fticrms.fticrms_page'))

@fticrms.route('/ftms/results_modal/<data_id>/<param_id>', methods=['GET'])
@login_required
def ftms_results_modal(data_id, param_id):

    ftmsresults = current_user.ftms_results.filter(FTMS_Result.id == data_id).first()

    if ftmsresults:
        tab_widget = generate_ftms_plots(ftmsresults)

        js_resources = INLINE.render_js()
        # css_resources = INLINE.render_css()
        scripts_divs = list()

        scripts_divs.append(components(tab_widget))

        down_href = url_for('fticrms.download_table', id=data_id)
        html = render_template(
            'workflows/fticr/ftms_plot_modal.html',
            script_list=scripts_divs,
            js_resources=js_resources,
            down_href=down_href)

        return html
    else:
        return redirect(url_for('fticrms.fticrms_page'))

@fticrms.route('/ftms/remove_result/<id>', methods=['GET'])
@login_required
def remove_result(id):

    ftmsresults = current_user.ftms_results.filter(FTMS_Result.id == id).first()
    if ftmsresults:
        db.session.delete(ftmsresults)

    db.session.commit()

    return Response(status=204)

def save_file(file_list, is_centroid=False):

    for file in file_list:
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':

            pass
            # flash('File name is empty')

        if file and allowed_file(file.filename):

            # save the file in the server tmp store
            add_data_db_and_save(file, is_centroid=is_centroid)

@fticrms.route('/ftms/upload', methods=['GET', 'POST'])
@login_required
def upload():

    ftms_input_form = FtmsFileInputForm()

    if ftms_input_form.validate_on_submit():

        storage_list = list(request.files.getlist("bruker_files"))

        if storage_list[0].filename:

            save_folder(storage_list)

        cal_file = request.files['cal_ref_file']

        if cal_file and allowed_file(cal_file.filename, calibration=True):

            add_data_db_and_save(cal_file)
            # cal_file.save(destination)
            # parameters.calibration_ref_filepath = str(destination)

        thermo_files = request.files.getlist("files")
        profile_files = request.files.getlist("profile_file")
        centroid_files = request.files.getlist("centroid_file")

        save_file(thermo_files, is_centroid=False)
        save_file(profile_files, is_centroid=False)
        save_file(centroid_files, is_centroid=True)

        return {'status': 'success'}, 202

        # return render_template('workflows/fticr/file_upload.html', ftms_input_form=ftms_input_form)
    else:
        return ftms_input_form.errors, 404

    return redirect(url_for('fticrms.fticrms_page'))

@fticrms.route('/ftms/combine_result/<ids>/<variable>', methods=['GET'])
@login_required
def combine_result(ids, variable):
    
    variable = variable.replace("_", '/')
    
    print(variable)
    
    data_ids = ids.split(sep=",")
    #variable = 'Peak Height'
    master_data_dict = []
    list_results_names = []
    
    date_time = datetime.now()
    utc_now = pytz.utc.localize(date_time)
    pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
    
    for data_id in data_ids:

        ftmsresults = current_user.ftms_results.filter(FTMS_Result.id == data_id).first()
        df = ftmsresults.to_dataframe()
        
        #select molecular formula with highest Confidence Score
        idx = df.groupby(['Molecular Formula'])['Confidence Score'].transform(max) == df['Confidence Score']
        df = df[idx]
        df.fillna(0, inplace=True)

        name_column = "{} ({} {})".format(variable, ftmsresults.name, ftmsresults.modifier)
        df.rename({variable: name_column}, inplace=True, axis=1)

        list_results_names.append(name_column)
        master_data_dict.extend(df.to_dict('records'))

    upload_location = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)
    filename_path = upload_location / '{} of Common Molecular Formulae - {}'.format(variable.replace("/", "_"), pst_now)
    filename = filename_path.with_suffix(('.csv'))
    filename.parent.mkdir(exist_ok=True, parents=True)

    #molsearch = ftmsresults.parameters_json.get("MolecularFormulaSearch")
    #output_min_score = molsearch.get("output_min_score")
    print('start merge')
    df = merge_records_results_table(master_data_dict, list_results_names)
    print('Done Merging')
    df.to_csv(filename)
    print('Done')
    @after_this_request
    def remove_file(response):
        try:
            filename.unlink()
        except Exception as error:
            print("Error removing or closing downloaded file handle", error)
        return response
    print('sent')
    return send_from_directory(upload_location,
                            filename.name, as_attachment=True)
    
    
@fticrms.route('/ftms/download_data/<id>', methods=['GET', 'POST'])
@login_required
def download_data(id):

    ftms_data = current_user.ftms_data.filter(FTMS_Data.id == id).first()
    if ftms_data:
        key = ftms_data.filepath
        upload_location = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)
        full_target_path = upload_location / ftms_data.filename
        full_target_path.parent.mkdir(exist_ok=True, parents=True)
        s3.Bucket('fticr-data').download_file(str(key), str(full_target_path))

        @after_this_request
        def remove_file(response):
            try:
                full_target_path.unlink()
            except Exception as error:
                print("Error removing or closing downloaded file handle", error)
            return response

        return send_from_directory(upload_location,
                                    ftms_data.filename, as_attachment=True)
        # url = s3_client.generate_presigned_url('get_object', Params={'Bucket': 'fticr-data', 'Key': "{}/{}".format(ftms_data.directory, ftms_data.filename)}, ExpiresIn=100)
        # return redirect(url, code=302)

    return Response(status=204)

@fticrms.route('/ftms/remove_data/<id>', methods=['GET', 'POST'])
@login_required
def remove_data(id):

    ftms_data = current_user.ftms_data.filter(FTMS_Data.id == id).first()

    if ftms_data:
        s3path = S3Path('/fticr-data/' + ftms_data.filepath)
        if s3path.exists():
            if s3path.is_dir():

                S3Path('/fticr-data/' + ftms_data.filepath).rmdir()
            else:
                S3Path('/fticr-data/' + ftms_data.filepath).unlink()
                # Path(ftms_data.filepath).unlink()

        # clear access links table from table that is being removed
        delete_accessLinks = FTMS_DataAccessLink.__table__.delete().where(FTMS_DataAccessLink.ftms_data_id == ftms_data.id)
        db.session.execute(delete_accessLinks)

        db.session.delete(ftms_data)
        db.session.commit()
        # res = make_response(jsonify({"message": "Collection created"}), 201)

    return Response(status=204)
    # res = make_response(jsonify({"message": "Collection created"}), 200)
    # return res

@fticrms.route('/ftms/load_data_modal/<data_id>/<param_id>', methods=['GET'])
@login_required
def load_data_modal(data_id, param_id):

    ftms_data = current_user.ftms_data.filter(FTMS_Data.id == data_id).first()

    if ftms_data:
        tab_widget = run_load_data(data_id, param_id)
        js_resources = INLINE.render_js()
        # css_resources = INLINE.render_css()
        scripts_divs = list()

        scripts_divs.append(components(tab_widget))

        down_href = url_for('fticrms.download_data', id=data_id)
        html = render_template(
            'workflows/fticr/ftms_plot_modal.html',
            script_list=scripts_divs,
            js_resources=js_resources,
            down_href=down_href)

        return html
    else:
        return redirect(url_for('fticrms.fticrms_page'))

@fticrms.route('/ftms/load_data/<id>', methods=['GET'])
@login_required
def load_data(id):

    ftms_data = current_user.ftms_data.filter(FTMS_Data.id == id).first()

    if ftms_data:

        tab_widget = run_load_data(id)
        js_resources = INLINE.render_js()
        # css_resources = INLINE.render_css()
        scripts_divs = list()

        scripts_divs.append(components(tab_widget))

        down_href = url_for('fticrms.download_data', id=id)
        html = render_template(
            'workflows/fticr/ftms_plots.html',
            script_list=scripts_divs,
            js_resources=js_resources,
            down_href=down_href)

        return Response(status=202)
    else:
        return redirect(url_for('fticrms.fticrms_page'))

@fticrms.route('/ftms/ftms_all_data')
@login_required
def ftms_all_data():

    all_ftms_data = current_user.ftms_data
    all_data_dict = [data.to_dict() for data in all_ftms_data.all()]

    return {'status': 'OK', 'data': all_data_dict}

@fticrms.route('/ftms/freda/<id>', methods=['GET'])
@login_required
def send_results_freda(id):

    ftmsresults = current_user.ftms_results.filter(FTMS_Result.id == id).first()

    df = ftmsresults.to_dataframe()

    result = df.to_json(orient='records')
    parsed = json.loads(result)
    # pretty print
    output = json.dumps(parsed, sort_keys=False, indent=4, separators=(',', ': '))
    # output = re.sub(r'",\s+', '", ', output)
    output.replace("\\", "\n")
    # send post here with request
    # get freda url as response and redirect to that page
    return redirect("freda_url")

@fticrms.route('/ftms/download/<id>', methods=['GET'])
@login_required
def download_table(id):

    ftmsresults = current_user.ftms_results.filter(FTMS_Result.id == id).first()
    
    upload_location = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)
    filename_path = upload_location / "{} {}".format(ftmsresults.name, ftmsresults.modifier)
    filename = filename_path.with_suffix(('.csv'))
    filename.parent.mkdir(exist_ok=True, parents=True)

    #molsearch = ftmsresults.parameters_json.get("MolecularFormulaSearch")
    #output_min_score = molsearch.get("output_min_score")

    df = ftmsresults.to_dataframe()
    
    #rslt_df = df.loc[df['Confidence Score'] > output_min_score]

    '''implement it to save to json format
    #result = df.to_json(orient='records')
    #parsed = json.loads(result)
    with open(filename, 'w', encoding='utf8', ) as outfile:

        import re
        #pretty print 
        output = json.dumps(parsed, sort_keys=False, indent=4, separators=(',', ': '))
        # output = re.sub(r'",\s+', '", ', output)
        output.replace("\\", "\n")
        outfile.write(output)
    '''
    df.to_csv(filename)

    @after_this_request
    def remove_file(response):
        try:
            filename.unlink()
        except Exception as error:
            print("Error removing or closing downloaded file handle", error)
        return response

    return send_from_directory(upload_location,
                               filename.name, as_attachment=True)


@fticrms.route('/ftms/download_results_params/<id>', methods=['GET'])
@login_required
def download_results_params(id):

    ftmsresults = current_user.ftms_results.filter(FTMS_Result.id == id).first()

    upload_location = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)
    filename_path = upload_location / str(ftmsresults.name)
    filename = filename_path.with_suffix(('.yml'))
    filename.parent.mkdir(exist_ok=True, parents=True)

    with open(filename, 'w', encoding='utf8', ) as outfile:

        output = ftmsresults.parameters_yaml
        outfile.write(output)
    
    @after_this_request
    def remove_file(response):
        try:
            filename.unlink()
        except Exception as error:
            print("Error removing or closing downloaded file handle", error)
        return response

    return send_from_directory(upload_location,
                               filename.name, as_attachment=True)


def start_ftms_result(file_id):

    # get class objs
    file_class = current_user.ftms_data.filter(FTMS_Data.id == file_id).first()

    file_result = current_user.ftms_results.filter_by(name=file_class.name).order_by(FTMS_Result.id.desc()).first()

    # data already exist
    duplicated_modifier = ""

    if file_result:

        if file_result.id > 0:

            duplicated_modifier = " [{}]".format(file_result.id + 1)

    ftmsresults = FTMS_Result(user_id=current_user.id,
                              name=file_class.name,
                              modifier=duplicated_modifier,
                              data_id=file_id,
                              status='Queued')

    db.session.add(ftmsresults)
    db.session.commit()

    return ftmsresults.id

@fticrms.route('/ftms/process/<parameters_id>', methods=['GET', 'POST'])
@login_required
def process_ftms(parameters_id):

    # from celery import group
    # from time import sleep
    
    ftms_submit_form = FTMSSubmitJob()

    if ftms_submit_form.validate_on_submit():

        list_id_data_process = ftms_submit_form.data_to_process.data

        id_cal_file = ftms_submit_form.reference_file.data

        args = ([int(current_user.id), item, id_cal_file, int(parameters_id), start_ftms_result(item)] for item in list_id_data_process)

        # TODO change this scope to data api, or execution api
        list_submitted_ids = []

        for each_data in args:

            task = run_direct_infusion_workflow.apply_async(args=[each_data], ignore_result=True, queue='ftms.di')
            each_data.append(task.id)
            task.get()
            list_submitted_ids.append(each_data)

        # tasks = list(run_direct_infusion_workflow.s((current_user.id, item, id_cal_file)) for item in list_id_data_process)

        # jobs = group(tasks)

        # result = jobs.apply_async()
        # result.save()

        # from celery.result import GroupResult
        # saved_result = GroupResult.restore(result.id)
        # print(result.id)
        # print(saved_result)
        # while not tasks[-1].ready():
        #    print(tasks[-1].id)
        #    print(tasks[-1].status)

        # run_direct_infusion_workflow.delay(list_id_data_process, id_cal_file)

        return {'status': 'submitted', 'list_submitted_ids': list_submitted_ids}, 202

    else: return ftms_submit_form.errors, 400

    return redirect(url_for('fticrms.fticrms_page'))

@fticrms.route('/ftms/parameters/all/<id>')
@login_required
def get_all_parameter_forms(id):

    ftms_parameters = current_user.ftms_parameters.filter(FTMS_Parameters.id == id).first()
    if not ftms_parameters:
        return 'Ups, did not find preset with id : {}'.format(id), 400

    basic_form = populate_basic_form(ftms_parameters=ftms_parameters)
    input_data_form = populate_input_settings_form(ftms_parameters=ftms_parameters)
    advanced_form = populate_advanced_form(ftms_parameters=ftms_parameters)
    ms_form = populate_ms_form(ftms_parameters=ftms_parameters)
    mspeak_form = populate_mspeak_form(ftms_parameters=ftms_parameters)
    transient_form = populate_transient_form(ftms_parameters=ftms_parameters)

    basic_html = render_template('workflows/fticr/basic_form.html', basic_form=basic_form)
    advanced_html = render_template('workflows/fticr/advanced_form.html', advanced_form=advanced_form)
    input_data_html = render_template('workflows/fticr/input_data_form.html', ftms_input_settings_form=input_data_form)
    ms_html = render_template('workflows/fticr/ms_form.html', ms_form=ms_form)
    mspeak_html = render_template('workflows/fticr/ms_peak_form.html', ms_peak_form=mspeak_form)
    transient_html = render_template('workflows/fticr/transient_form.html', transient_form=transient_form)

    return {'done': 'Successfully loaded parameters for preset: {}'.format(ftms_parameters.name),
            'basic': basic_html,
            'input': input_data_html,
            'advanced': advanced_html,
            'ms': ms_html,
            'mspeak': mspeak_html,
            'transient': transient_html,
            }, 202

@fticrms.route('/ftms/parameters/remove-preset/<id>', methods=['PUT'])
@login_required
def remove_preset(id):

    ftms_params = current_user.ftms_parameters.filter(FTMS_Parameters.id == id).first()
    if ftms_params:
        db.session.delete(ftms_params)
        db.session.commit()
        res = {"done": "Preset successfully removed"}, 202
    else:
        res = "Preset not found", 400
    return res

@fticrms.route('/ftms/parameters/add-preset', methods=['POST'])
@login_required
def add_preset():

    if request.method == 'POST':

        preset_name = request.json.get("name")

        parameter_obj = current_user.ftms_parameters.filter_by(name=preset_name).first()

        if parameter_obj:

            return 'error:  {} name already exists'.format(preset_name), 409

        '''basic form'''

        basic_data = request.json.get("basic")
        clean_data = clean_dict(basic_data)
        basic_form = BasicFtmsSettingsForm(MultiDict(basic_data))
        basic_dict = basic_form_to_dict(basic_form, clean_data)
        '''input settings form'''

        input_settings_data = request.json.get("input")
        input_settings_dict = clean_dict(input_settings_data)

        '''advanced form'''

        advanced_data = request.json.get("advanced")
        clean_data = clean_dict(advanced_data)

        advanced_form = AdvancedFtmsSettingsForm(MultiDict(advanced_data))

        advanced_dict = advanced_form_to_dict(advanced_form, clean_data)
        # parameter_obj.basic_parameters = json.dumps(clean_data)

        '''ms form'''

        ms_data = request.json.get("ms")
        ms_dict = clean_dict(ms_data)

        ms_form = MassSpectrumSettingForm(MultiDict(ms_data))

        '''transient form'''

        transient_data = request.json.get("transient")
        transient_dict = clean_dict(transient_data)

        '''mspeak form'''

        mspeak_data = request.json.get("mspeak")
        clean_data = clean_dict(mspeak_data)

        ms_peak_form = MassSpecPeakSettingForm(MultiDict(mspeak_data))

        mspeak_dict = mspeak_form_to_dict(ms_peak_form, clean_data)

        new_preset = FTMS_Parameters(user_id=current_user.id,
                                     name=preset_name,
                                     basic_parameters=json.dumps(basic_dict),
                                     advanced_parameters=json.dumps(advanced_dict),
                                     ms_parameters=json.dumps(ms_dict),
                                     ms_peak_parameters=json.dumps(mspeak_dict),
                                     transient_parameters=json.dumps(transient_dict),
                                     input_data_parameters=json.dumps(input_settings_dict)
                                     )

        db.session.add(new_preset)
        db.session.commit()
        return {'id': '{}'.format(new_preset.id)}, 202
        # parameter_obj = current_user.ftms_parameters.filter_by(name=preset_name).first()

        # if parameter_obj:

        #    return {'error': "{} name already exists".format(preset_name)}, 409

        # else:

        #    parameter_obj = current_user.ftms_parameters.filter_by(name='default').first()


@fticrms.route('/ftms/update-parameters/<parameter_type>/<parameter_id>', methods=['GET', 'POST'])
@login_required
def update_basic_parameters(parameter_type, parameter_id):

    parameter_obj = current_user.ftms_parameters.filter(FTMS_Parameters.id == parameter_id).first()

    def success_message():

        return {'done': 'Successfully updated parameters for preset: {}'.format(parameter_obj.name)}, 200

    if request.method == 'GET':

        return {'done': 'Parameters not updated for preset: {}, Please try again'.format(parameter_obj.name)}, 200

    elif request.method == 'POST':

        if not parameter_obj:
            return Response(status=404)

        # ms_form = MassSpectrumSettingForm()
        # transient_form = TransientSettingForm()
        # ms_peak_form = MassSpecPeakSettingForm()

        if parameter_type == 'ftmsbasicsettings':

            basic_form = BasicFtmsSettingsForm()
            if basic_form.validate_on_submit():

                clean_data = clean_form(request.form)

                basic_dict = basic_form_to_dict(basic_form, clean_data)
                parameter_obj.basic_parameters = json.dumps(basic_dict)

                db.session.commit()

                return success_message()

            else:

                return basic_form.errors, 404

        elif parameter_type == 'ftmsadvancedsettings':

            advanced_form = AdvancedFtmsSettingsForm()

            if advanced_form.validate_on_submit():

                clean_data = clean_form(request.form)

                advanced_dict = advanced_form_to_dict(advanced_form, clean_data)

                parameter_obj.advanced_parameters = json.dumps(advanced_dict)
                db.session.commit()

                return success_message()

            else:

                return advanced_form.errors, 404

        elif parameter_type == 'ftmssettings':

            ms_form = MassSpectrumSettingForm()
            if ms_form.validate_on_submit():

                clean_data = clean_form(request.form)
                parameter_obj.ms_parameters = json.dumps(clean_data)
                db.session.commit()

                return success_message()

            else:

                return ms_form.errors, 404

        elif parameter_type == 'ftmstransietsettings':

            transient_form = TransientSettingForm()
            if transient_form.validate_on_submit():

                clean_data = clean_form(request.form)

                parameter_obj.transient_parameters = json.dumps(clean_data)
                db.session.commit()

                return success_message()

            else:

                return transient_form.errors, 404

        elif parameter_type == 'ftmsinputdatasettings':

            inputsettings_form = DataInputSettingForm()
            if inputsettings_form.validate_on_submit():

                clean_data = clean_form(request.form)

                parameter_obj.input_data_parameters = json.dumps(clean_data)
                db.session.commit()

                return success_message()

            else:

                return inputsettings_form.errors, 404

        elif parameter_type == 'ftmspeaksettings':

            ms_peak_form = MassSpecPeakSettingForm()

            if ms_peak_form.validate_on_submit():

                kendrick_base = {}
                clean_data = clean_form(request.form)

                mspeak_dict = mspeak_form_to_dict(ms_peak_form, clean_data)

                parameter_obj.ms_peak_parameters = json.dumps(mspeak_dict)
                db.session.commit()

                return success_message()

            else:

                return ms_peak_form.errors, 404

        else:

            return Response(404)


@fticrms.route('/ftms', methods=['GET', 'POST'])
@login_required
def fticrms_page():

    ftms_input_form = FtmsFileInputForm()

    ftms_submit_form = FTMSSubmitJob()

    basic_form = populate_basic_form()

    advanced_form = populate_advanced_form()

    ftms_input_settings_form = populate_input_settings_form()

    ms_form = populate_ms_form()

    ms_peak_form = populate_mspeak_form()

    transient_form = populate_transient_form()

    # presets needs to be after all the forms generation
    presets_form = ParametersPresetsForm()

    all_ftms_data = current_user.ftms_data.order_by(FTMS_Data.id.desc()).all()
    all_ftms_result = current_user.ftms_results.order_by(FTMS_Result.id.desc()).all()
    return render_template('workflows/fticr/ftms_workflow.html', presets_form=presets_form,
                                                                 ftms_submit_form=ftms_submit_form,
                                                                 ftms_input_form=ftms_input_form,
                                                                 ftms_input_settings_form=ftms_input_settings_form,
                                                                 basic_form=basic_form,
                                                                 ms_form=ms_form,
                                                                 advanced_form=advanced_form,
                                                                 ms_peak_form=ms_peak_form,
                                                                 transient_form=transient_form,
                                                                 ftms_results=all_ftms_result,
                                                                 ftms_data=all_ftms_data)

def save_folder(storage_list):

    upload_folder = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)
    upload_folder.mkdir(parents=True, exist_ok=True)

    dirname = Path(storage_list[0].filename).parents[0]

    all_ftms_data = current_user.ftms_data
    filename_count = all_ftms_data.filter(FTMS_Data.name == str(dirname)).count()

    if filename_count > 0:
        #  TODO change the name and modifier or delete the file
        pass

    s3_dir_path = "{}/{}".format(str(current_user.id), dirname)
    for file_storage in storage_list:
        # filename = secure_filename(file_storage.filename)
        # filepath = str(upload_folder / filename)
        # new_file = Path(filepath)
        filename = file_storage.filename
        new_file = upload_folder / Path(filename)

        directory = new_file.parent
        directory.mkdir(parents=True, exist_ok=True)

        file_storage.save(new_file)

        s3_path = "{}/{}".format(current_user.id, filename)
        minio.fput_object('fticr-data', s3_path, str(new_file))
        # try:
        #    s3.Bucket('fticr-data').upload_file(str(new_file), s3_path)
        # except Exception:
        #    print(s3_path)
        new_file.unlink()

    ftms_data = FTMS_Data(user_id=current_user.id, name=str(dirname), filepath=s3_dir_path, modifier='')
    db.session.add(ftms_data)
    db.session.commit()

def add_data_db_and_save(file, is_centroid=True, access_group_name='Private'):
    '''file = request.file'''
    # define and create the upload folder for current user
    upload_folder = Path(current_app.config['UPLOAD_FOLDER'])

    filename = secure_filename(file.filename)
    filepath = str(upload_folder / filename)
    # save the file in the server tmp store

    new_file = Path(filepath)
    all_ftms_data = current_user.ftms_data

    filename_count = all_ftms_data.filter(FTMS_Data.name == str(new_file.stem)).count()

    access_group = db.session.query(AccessGroup).filter(AccessGroup.name == access_group_name).first()

    if not access_group:
        access_group = AccessGroup(name=access_group_name)
        db.session.add(access_group)
        db.session.commit()

    # data already exist
    if filename_count > 0:

        next_id = f" ({filename_count})"

        modified_path = (new_file.parent / (new_file.stem + f"_{next_id}")).with_suffix(new_file.suffix)
        modified_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(modified_path)
        s3_path = "{}/{}".format(current_user.id, modified_path.name)
        # s3.Bucket('fticr-data').upload_file(str(modified_path), s3_path)
        minio.fput_object('fticr-data', s3_path, str(modified_path))
        modified_path.unlink()

        ftms_data = FTMS_Data(user_id=current_user.id, name=str(new_file.stem),
                              filepath=str(s3_path), modifier=next_id, is_centroid=is_centroid)

        group_data_assoc = FTMS_DataAccessLink()
        group_data_assoc.ftms_data = ftms_data

        access_group.ftms_all_data.append(group_data_assoc)
        db.session.commit()

    else:

        new_file.parent.mkdir(parents=True, exist_ok=True)
        file.save(new_file)
        s3_path = "{}/{}".format(current_user.id, filename)
        # s3.Bucket('fticr-data').upload_file(str(new_file), "{}/{}".format(current_user.id, file.filename))
        minio.fput_object('fticr-data', s3_path, str(new_file))
        new_file.unlink()

        ftms_data = FTMS_Data(user_id=current_user.id, name=str(new_file.stem), filepath=s3_path, modifier='', is_centroid=is_centroid)

        group_data_assoc = FTMS_DataAccessLink()
        group_data_assoc.ftms_data = ftms_data
        access_group.ftms_all_data.append(group_data_assoc)
        db.session.commit()

def merge_records_results_table(master_data_dict,  list_results_names):

    formula_dict = {}
    for record in master_data_dict:
        molecular_formula = record.get('Molecular Formula')
        
        if molecular_formula in formula_dict.keys():
            formula_dict[molecular_formula].append(record)
        else:
            formula_dict[molecular_formula] = [record]
    
    merged_records = []
    
    excluded_keys = ['m/z', 'Calibrated m/z', 'Calculated m/z', 'Peak Area', 'Resolving Power', 'S/N', 'm/z Error (ppm)', 'm/z Error Score', 
                    'Isotopologue Similarity', 'Mono Isotopic Index', 'Confidence Score']
    excluded_keys.extend(list_results_names)

    merged_records = []
    for formula, records in formula_dict.items():
        
        merged_dict = {}
        for filename in list_results_names:
            merged_dict[filename] = nan
        
        #get the commun variable from all records
        for record in  records: 
            #than get the rest of the data
            for filename in list_results_names:
                if filename in record.keys():
                    merged_dict[filename] = record[filename]
            for key in record.keys():
                if key not in excluded_keys:
                    merged_dict[key] = record[key]
    
        merged_records.append(merged_dict)
    
    master_df = DataFrame(merged_records)
    master_df.set_index('Molecular Formula', inplace=True)
    return master_df