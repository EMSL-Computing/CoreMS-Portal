import time
from pathlib import Path
import json


from bokeh.embed import components
from bokeh.resources import INLINE
from flask import request, redirect, render_template, url_for, after_this_request
from flask import Blueprint, send_from_directory, Response
from flask import current_app
from flask_login import login_required, current_user
from s3path import S3Path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import MultiDict

from app import db, minio, s3_client, s3

from app.blueprints.gcms.gcms_form_methods import allowed_gcms_file, populate_gcms_compound_search_form, populate_gcms_signal_form
from app.blueprints.ftms.ftms_forms import clean_dict, clean_form

from app.models.auth_models import AccessGroup
from app.models.gcms_model import GCMS_Data, GCMS_Result, GCMS_DataAccessLink, GCMS_Parameters

from app.forms.gcms_forms import GcmsFileInputForm, GcmsParametersPresetsForm, GcmsSubmitJob
from app.forms.gcms_forms import CompoundSearchSettingsForm, GasChromatographSettingForm

from app.workflows.gcms.gcms_workflow import run_gcms_metabolomics_workflow
from app.workflows.gcms.gcms_workflow import generate_gcms_plots
from app.workflows.gcms.gcms_open_data import run_load_gcms_data

gcms = Blueprint('gcms', __name__)

@gcms.route('/gcms', methods=['GET', 'POST'])
@login_required
def gcms_page():

    gcms_upload_form = GcmsFileInputForm()

    gcms_peak_detection_form = populate_gcms_signal_form()

    gcms_molecular_search_form = populate_gcms_compound_search_form()

    gcms_process_form = GcmsSubmitJob()

    gcms_presets_form = GcmsParametersPresetsForm()

    all_gcms_data = current_user.gcms_data.order_by(GCMS_Data.id.desc()).all()

    all_gcms_result = current_user.gcms_results.order_by(GCMS_Result.id.desc()).all()

    return render_template('workflows/gcms/gcms_workflow.html', gcms_upload_form=gcms_upload_form,
                                                                gcms_data=all_gcms_data,
                                                                gcms_presets_form=gcms_presets_form,
                                                                gcms_peak_detection_form=gcms_peak_detection_form,
                                                                gcms_molecular_search_form=gcms_molecular_search_form,
                                                                gcms_process_form=gcms_process_form,
                                                                gcms_results=all_gcms_result)

@gcms.route('/gcms/upload', methods=['GET', 'POST'])
@login_required
def upload():

    gcms_upload_form = GcmsFileInputForm()

    if gcms_upload_form.validate_on_submit():

        cal_file = request.files['gcms_cal_ref_file']

        if cal_file and allowed_gcms_file(cal_file.filename):

            add_data_db_and_save(cal_file, calibration=True)

        files = request.files.getlist("gcms_files")
        files_path = []
        input_type_list = []

        for file in files:
            # if user does not select file, browser also
            # submit an empty part without filename

            if file.filename == '':

                pass
                # flash('File name is empty')

            if file and allowed_gcms_file(file.filename):

                # save the file in the server tmp store
                add_data_db_and_save(file)

        return {'status': 'success'}, 202

    else:

        return gcms_upload_form.errors, 404

    return redirect(url_for('gcms.gcms_page'))

@gcms.route('/gcms/download_data/<id>', methods=['GET', 'POST'])
@login_required
def download_data(id):

    gcms_data = current_user.gcms_data.filter(GCMS_Data.id == id).first()
    if gcms_data:
        key = gcms_data.filepath
        upload_location = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)
        full_target_path = upload_location / gcms_data.filename
        full_target_path.parent.mkdir(exist_ok=True, parents=True)
        s3.Bucket('gcms-data').download_file(str(key), str(full_target_path))

        @after_this_request
        def remove_file(response):
            try:
                full_target_path.unlink()
            except Exception as error:
                print("Error removing or closing downloaded file handle", error)
            return response

        return send_from_directory(upload_location,
                                    gcms_data.filename, as_attachment=True)
        # url = s3_client.generate_presigned_url('get_object', Params={'Bucket': 'fticr-data', 'Key': "{}/{}".format(ftms_data.directory, ftms_data.filename)}, ExpiresIn=100)
        # return redirect(url, code=302)

    return Response(status=204)

@gcms.route('/gcms/remove_data/<id>', methods=['GET', 'POST'])
@login_required
def remove_data(id):

    gcms_data = current_user.gcms_data.filter(GCMS_Data.id == id).first()

    if gcms_data:
        s3path = S3Path('/gcms-data/' + gcms_data.filepath)
        if s3path.exists():
            s3path.unlink()

        delete_accessLinks = GCMS_DataAccessLink.__table__.delete().where(GCMS_DataAccessLink.gcms_data_id == gcms_data.id)
        db.session.execute(delete_accessLinks)

        db.session.delete(gcms_data)
        db.session.commit()

    return Response(status=204)

@gcms.route('/gcms/load_data_modal/<id>', methods=['GET'])
@login_required
def load_data_modal(id):

    gcms_data = current_user.gcms_data.filter(GCMS_Data.id == id).first()

    if gcms_data:
        tab_widget = run_load_gcms_data(id)
        js_resources = INLINE.render_js()
        # css_resources = INLINE.render_css()
        scripts_divs = list()

        scripts_divs.append(components(tab_widget))

        down_href = url_for('gcms.download_data', id=id)
        html = render_template(
            'workflows/gcms/gcms_plot_modal.html',
            script_list=scripts_divs,
            js_resources=js_resources,
            down_href=down_href)

        return html
    else:
        return redirect(url_for('gcms.gcms_page'))


@gcms.route('/gcms/gcms_all_data')
@login_required
def gcms_all_data():

    gcms_all_data = current_user.gcms_data
    all_data_dict = [data.to_dict() for data in gcms_all_data.all()]

    return {'status': 'OK', 'data': all_data_dict}

@gcms.route('/gcms/parameters/all/<id>')
@login_required
def get_all_parameter_forms(id):

    gcms_parameters = current_user.gcms_parameters.filter(GCMS_Parameters.id == id).first()

    if not gcms_parameters:
        return 'Ups, did not find preset with id : {}'.format(id), 400

    molsearch_form = populate_gcms_compound_search_form(gcms_parameters=gcms_parameters)
    peakdetection_form = populate_gcms_signal_form(gcms_parameters=gcms_parameters)

    molsearch_html = render_template('workflows/gcms/parameter/gcms_molecular_search.html', gcms_molecular_search_form=molsearch_form)
    peakdetection_html = render_template('workflows/gcms/parameter/gcms_peak_detection.html', gcms_peak_detection_form=peakdetection_form)

    return {'done': 'Successfully loaded parameters for preset: {}'.format(gcms_parameters.name),
            'molsearch': molsearch_html,
            'peakdetection': peakdetection_html,
            }, 202


@gcms.route('/gcms/parameters/remove-preset/<id>', methods=['PUT'])
@login_required
def remove_preset(id):

    print()
    gcms_params = current_user.gcms_parameters.filter(GCMS_Parameters.id == id).first()
    if gcms_params:
        db.session.delete(gcms_params)
        db.session.commit()
        res = {"done": "Preset successfully removed"}, 202
    else:
        res = "Preset not found", 400
    return res

@gcms.route('/gcms/parameters/add-preset', methods=['POST'])
@login_required
def add_preset():

    if request.method == 'POST':

        preset_name = request.json.get("name")

        parameter_obj = current_user.gcms_parameters.filter_by(name=preset_name).first()

        if parameter_obj:

            return 'error:  {} name already exists'.format(preset_name), 409

        '''basic form'''

        '''CompoundSearchSettings Form '''

        molsearch_data = request.json.get("molsearch")
        molsearch_dict = clean_dict(molsearch_data)
        molsearch_form = CompoundSearchSettingsForm(MultiDict(molsearch_data))
        molsearch_dict['exploratory_mode'] = molsearch_form.data.get('exploratory_mode')

        '''GasChromatographSetting Form '''

        peakdetection_data = request.json.get("peakdetection")
        peakdetection_dict = clean_dict(peakdetection_data)
        peakdetection_form = GasChromatographSettingForm(MultiDict(peakdetection_data))
        peakdetection_dict['use_deconvolution'] = peakdetection_form.data.get('use_deconvolution')

        '''create preset '''

        new_preset = GCMS_Parameters(user_id=current_user.id,
                                     name=preset_name,
                                     basic_parameters=json.dumps(molsearch_dict),
                                     advanced_parameters=json.dumps(peakdetection_dict),
                                     )

        db.session.add(new_preset)
        db.session.commit()
        return {'id': '{}'.format(new_preset.id)}, 202

@gcms.route('/gcms/update-parameters/<parameter_type>/<parameter_id>', methods=['POST'])
@login_required
def update_gcms_parameters(parameter_type, parameter_id):

    def success_message():

        return {'done': 'Successfully updated parameters for preset: {}'.format(parameter_obj.name)}, 202

    if request.method == 'POST':

        parameter_obj = current_user.gcms_parameters.filter(GCMS_Parameters.id == parameter_id).first()
        if not parameter_obj:
            return Response(status=404)

        # ms_form = MassSpectrumSettingForm()
        # transient_form = TransientSettingForm()
        # ms_peak_form = MassSpecPeakSettingForm()

        if parameter_type == 'gcmsmolecularsearchsettings':

            molsearch_form = CompoundSearchSettingsForm()

            if molsearch_form.validate_on_submit():

                clean_data = clean_form(request.form)

                clean_data['exploratory_mode'] = molsearch_form.data.get('exploratory_mode')

                parameter_obj.basic_parameters = json.dumps(clean_data)
                db.session.commit()

                return success_message()

            else:

                return molsearch_form.errors, 404

        elif parameter_type == 'gcmspeakdetectionsettings':

            peakdetection_form = GasChromatographSettingForm()

            if peakdetection_form.validate_on_submit():

                clean_data = clean_form(request.form)

                clean_data['use_deconvolution'] = peakdetection_form.data.get('use_deconvolution')

                parameter_obj.advanced_parameters = json.dumps(clean_data)
                db.session.commit()

                return success_message()

            else:

                return peakdetection_form.errors, 404

        else:

            return Response(404)

def start_gcms_result(file_id):

    # get class objs
    file_class = current_user.gcms_data.filter(GCMS_Data.id == file_id).first()

    file_result = current_user.gcms_results.filter_by(name=file_class.name).order_by(GCMS_Result.id.desc()).first()

    # data already exist
    duplicated_modifier = ""

    if file_result:

        if file_result.id > 0:

            duplicated_modifier = " [{}]".format(file_result.id + 1)

    gcms_results = GCMS_Result(user_id=current_user.id,
                               name=file_class.name,
                               data_id=file_id,
                               modifier=duplicated_modifier,
                               status='Queued')

    db.session.add(gcms_results)
    db.session.commit()

    return gcms_results.id

@gcms.route('/gcms/process/<parameters_id>', methods=['GET', 'POST'])
@login_required
def process_gcms(parameters_id):

    # from celery import group
    # from time import sleep

    gcms_submit_form = GcmsSubmitJob()

    if gcms_submit_form.validate_on_submit():

        list_id_data_process = gcms_submit_form.gcms_data_to_process.data

        id_cal_file = gcms_submit_form.gcms_reference_file.data

        # adds task to postgresql database
        args = ([int(current_user.id), item, id_cal_file, int(parameters_id), start_gcms_result(item)] for item in list_id_data_process)

        list_submitted_ids = []

        for each_data in args:

            task = run_gcms_metabolomics_workflow.apply_async(args=[each_data], ignore_result=True, queue='gcms.lowres')
            each_data.append(task.id)
            task.get()
            list_submitted_ids.append(each_data)

        # tasks = list(run_gcms_metabolomics_workflow.s((current_user.id, item, id_cal_file)) for item in list_id_data_process)

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

        # run_gcms_metabolomics_workflow.delay(list_id_data_process, id_cal_file)

        return {'status': 'submitted', 'list_submitted_ids': list_submitted_ids}, 202

    else: return gcms_submit_form.errors

    return redirect(url_for('gcms.gcms_page'))

@gcms.route('/gcms/download/<id>', methods=['GET'])
@login_required
def download_table(id):

    gcms_results = current_user.gcms_results.filter(GCMS_Result.id == id).first()

    upload_location = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)
    filename_path = upload_location / "{} {}".format(gcms_results.name, gcms_results.modifier)
    filename = filename_path.with_suffix(('.csv'))
    filename.parent.mkdir(exist_ok=True, parents=True)

    df = gcms_results.to_dataframe()

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


@gcms.route('/gcms/download_results_params/<id>', methods=['GET'])
@login_required
def download_results_params(id):

    gcms_results = current_user.gcms_results.filter(GCMS_Result.id == id).first()

    upload_location = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)

    filename_path = upload_location / str(gcms_results.name)
    filename = filename_path.with_suffix(('.yml'))
    filename.parent.mkdir(exist_ok=True, parents=True)
    with open(filename, 'w', encoding='utf8', ) as outfile:

        output = gcms_results.parameters_yaml
        outfile.write(output)
        print(output)

    @after_this_request
    def remove_file(response):
        try:
            filename.unlink()
        except Exception as error:
            print("Error removing or closing downloaded file handle", error)
        return response

    return send_from_directory(upload_location,
                               filename.name, as_attachment=True)


@gcms.route('/gcms/results_modal/<id>', methods=['GET'])
@login_required
def gcms_results_modal(id):

    gcms_results = current_user.gcms_results.filter(GCMS_Result.id == id).first()

    if gcms_results:

        tab_widget = generate_gcms_plots(gcms_results)

        js_resources = INLINE.render_js()
        # css_resources = INLINE.render_css()
        scripts_divs = list()

        scripts_divs.append(components(tab_widget))

        down_href = url_for('gcms.download_table', id=id)
        html = render_template(
            'workflows/gcms/gcms_plot_modal.html',
            script_list=scripts_divs,
            js_resources=js_resources,
            down_href=down_href)

        return html
    else:
        return redirect(url_for('gcms.gcms_page'))


@gcms.route('/gcms/remove_result/<id>', methods=['GET'])
@login_required
def remove_result(id):

    gcms_result = current_user.gcms_results.filter(GCMS_Result.id == id).first()
    if gcms_result:
        db.session.delete(gcms_result)

    db.session.commit()

    return Response(status=204)


def add_data_db_and_save(file, calibration=False, access_group_name='Private'):
    '''file = request.file'''

    # define and create the upload folder for current user
    upload_folder = Path.cwd() / Path(current_app.config['UPLOAD_FOLDER']) / str(current_user.id)
    # create directory is it does not exist
    upload_folder.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file.filename)
    filepath = str(upload_folder / filename)
    # save the file in the server tmp store

    new_file = Path(filepath)

    all_gcms_data = current_user.gcms_data

    filename_count = all_gcms_data.filter(GCMS_Data.name == str(new_file.stem)).count()
    # data already exist

    access_group = db.session.query(AccessGroup).filter(AccessGroup.name == access_group_name).first()

    if not access_group:

        access_group = AccessGroup(name=access_group_name)
        db.session.commit()

    if filename_count > 0:

        next_id = " ({})".format(filename_count)
        modified_path = (new_file.parent / (new_file.stem + "_{}".format(next_id))).with_suffix(new_file.suffix)

        directory = modified_path.parent
        directory.mkdir(parents=True, exist_ok=True)

        file.save(modified_path)

        s3_path = "{}/{}".format(current_user.id, modified_path.name)

        minio.fput_object('gcms-data', s3_path, str(modified_path))

        modified_path.unlink()

        gcms_data = GCMS_Data(user_id=current_user.id, name=str(new_file.stem), filepath=str(s3_path), modifier=next_id)
        if calibration:
            gcms_data.is_calibration = True

        group_data_assoc = GCMS_DataAccessLink()
        group_data_assoc.gcms_data = gcms_data
        access_group.gcms_all_data.append(group_data_assoc)
        db.session.commit()

    else:

        directory = new_file.parent
        directory.mkdir(parents=True, exist_ok=True)

        file.save(new_file)

        s3_path = "{}/{}".format(current_user.id, filename)
        minio.fput_object('gcms-data', s3_path, str(new_file))
        new_file.unlink()

        gcms_data = GCMS_Data(user_id=current_user.id, name=str(new_file.stem), filepath=s3_path, modifier='')
        if calibration:
            gcms_data.is_calibration = True

        group_data_assoc = GCMS_DataAccessLink()
        group_data_assoc.gcms_data = gcms_data
        access_group.gcms_all_data.append(group_data_assoc)
        db.session.commit()
