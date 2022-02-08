
import dataclasses
from typing import Dict
import json
from pathlib import Path
from multiprocessing import Pool
import numpy as np

from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, HoverTool, DataTable, TableColumn, CustomJS, Slider, RangeSlider, CDSView, IndexFilter
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.palettes import turbo
import bokeh.models as bmo

from corems.mass_spectrum.calc.Calibration import MzDomainCalibration
from corems.mass_spectrum.input.massList import ReadMassList
from corems.molecular_id.search.molecularFormulaSearch import SearchMolecularFormulas
from corems.transient.input.brukerSolarix import ReadBrukerSolarix
from corems.encapsulation.factory.parameters import MSParameters
from corems.encapsulation.factory.processingSetting import DataInputSetting, LiqChromatographSetting, MassSpecPeakSetting, MassSpectrumSetting, MolecularFormulaSearchSettings, TransientSetting

from app import db
from app import celery
from app.models.auth_models import User
from app.workflows.gcms.bokeh_utils import plot_styler
from app.models.ftms_model import FTMS_Result
from app.config import Config
from s3path import S3Path


def error_plot(ftmsresults, df) -> figure:

    hover_tool = HoverTool(names=['ftms_error'], tooltips=[
        ("m/z", "@{m/z}{0.00000}"),
        ("error (ppm)", "@{m/z Error (ppm)}{0.0000}"),
        ("DBE", "@{DBE}{0.0}"),
        ("molecular formula", "@{Molecular Formula}"),
        ("confidence score", "@{Confidence Score}{0.00}"),
        ("m/z average error score", "@{m/z Error Score}{0.00}"),
        ("isotopologue similarity", "@{Isotopologue Similarity}{0.00}")
    ],
        formatters={
            '@date': 'datetime',        # use 'datetime' formatter for '@date' field
            '@{adj close}': 'printf',   # use 'printf' formatter for '@{adj close}' field
                                        # use default 'numeral' formatter for other fields
    },
        # display a tooltip whenever the cursor is vertically in line with a glyph
        mode='mouse')

    # df = df[df['m/z Error (ppm)'].notna()]
    # if df:
    # par = np.polyfit(df['m/z'], df['m/z Error (ppm)'], 1)
    # slope = par[0]
    # intercept = par[1]
    # y_pred = [slope * i + intercept for i in list(df['m/z'])]

    source = ColumnDataSource(df)

    amp_slider = RangeSlider(start=0.0, end=1, value=(0.0, 1.0), step=.01, title="Confidence Score less than:")

    fig = figure(title=ftmsresults.name, tools=["pan", "box_zoom", "wheel_zoom", "save", "reset", hover_tool])

    fig.xaxis.axis_label = "m/z"
    fig.yaxis.axis_label = "Error"

    # source1 = ColumnDataSource({'x': [], 'y': []})
    # sr = fig.circle(x='x', y='y', size=10, color="red", alpha=1.0, source=source1)
    # in_range=sr.data_source

    filters = IndexFilter(list(range(len(df))))
    view = CDSView(source=source, filters=[filters])

    scatter = fig.circle(x='m/z', y='m/z Error (ppm)', source=source, size=5, color="midnightblue", alpha=0.75, view=view, name='ftms_error')
    # fig.line(df['m/z'], y_pred, color='red', legend_label='y=' + str(round(slope, 2)) + 'x+' + str(round(intercept, 2)))

    callback = CustomJS(args=dict(source=source, filter=filters, amp=amp_slider, ),
                        code="""

        //const data = {'x': [], 'y': []}
        const indices = []
        for (var i = 0; i < source.get_length(); i++) {
            if (source.data['Confidence Score'][i] >= cb_obj.value[0] & source.data['Confidence Score'][i] <= cb_obj.value[1]) {
                //data['x'].push(source.data['m/z'][i])
                //data['y'].push(source.data['m/z Error (ppm)'][i])
                indices.push(i)
            }
        }
        filter.indices = indices
        //in_range.data = data
        source.change.emit()

    """)

    amp_slider.js_on_change('value', callback)

    fig.toolbar.logo = None
    fig.toolbar_location = "above"
    fig.legend.location = "top_right"
    fig.legend.click_policy = "hide"

    # plot_styler(fig, start_y=-1)
    fig.sizing_mode = "stretch_both"

    layout = column(
        fig,
        amp_slider,
    )
    layout.sizing_mode = "stretch_both"
    return layout

def vankrevelen_plot(ftmsresults, df) -> figure:

    hover_tool = HoverTool(names=['ftms_van'], tooltips=[
        ("m/z", "@{m/z}{0.00000}"),
        ("error (ppm)", "@{m/z Error (ppm)}{0.0000}"),
        ("DBE", "@{DBE}{0.0}"),
        ("molecular formula", "@{Molecular Formula}"),
        ("confidence score", "@{Confidence Score}{0.00}"),
        ("m/z error score", "@{m/z Error Score}{0.00}"),
        ("isotopologue similarity", "@{Isotopologue Similarity}{0.00}")

    ],
        formatters={
            '@date': 'datetime',        # use 'datetime' formatter for '@date' field
            '@{adj close}': 'printf',   # use 'printf' formatter for '@{adj close}' field
                                        # use default 'numeral' formatter for other fields
    },
        # display a tooltip whenever the cursor is vertically in line with a glyph
        mode='mouse')

    fig = figure(title=ftmsresults.name, tools=["pan", "box_zoom", "wheel_zoom", "save", "reset", hover_tool])
    df = df[df['m/z Error (ppm)'].notna()]
    normalized_peak_height = df['Peak Height'] / df['Peak Height'].max()

    df["normalized"] = (2 * np.sqrt(normalized_peak_height / np.pi)) * 40
    source = ColumnDataSource(df)

    fig.xaxis.axis_label = "O/C"
    fig.yaxis.axis_label = "H/C"

    filters = IndexFilter(list(range(len(df))))
    view = CDSView(source=source, filters=[filters])

    fig.scatter(x='O/C', y='H/C', source=source, size="normalized",
                color="midnightblue", alpha=0.5, name='ftms_van', view=view)

    fig.toolbar.logo = None
    fig.toolbar_location = "above"

    # plot_styler(fig, start_y=-1)
    fig.sizing_mode = "stretch_both"

    # source1 = ColumnDataSource({'x': [], 'y': []})
    # sr = fig.circle(x='x', y='y', size=10, color="red", alpha=1.0, source=source1)
    # in_range=sr.data_source

    amp_slider = RangeSlider(start=0.0, end=1, value=(0.0, 1.0), step=.01, title="Confidence Score less than:")
    callback = CustomJS(args=dict(source=source, amp=amp_slider, filter=filters),
                        code="""

        //const data = {'x': [], 'y': []}
        const indices = []
        for (var i = 0; i < source.get_length(); i++) {
            if (source.data['Confidence Score'][i] >= cb_obj.value[0] & source.data['Confidence Score'][i] <= cb_obj.value[1]) {
                //data['x'].push(source.data['O/C'][i])
                //data['y'].push(source.data['H/C'][i])
            indices.push(i)
            }
        }
        filter.indices = indices
        //in_range.data = data
        source.change.emit()

    """)

    amp_slider.js_on_change('value', callback)
    layout = column(
        fig,
        amp_slider,
    )
    layout.sizing_mode = "stretch_both"

    return layout

def class_plot(ftmsresults, df) -> figure:

    from bokeh.palettes import Spectral10, small_palettes
    # from bokeh.models import Range1d
    from natsort import natsorted
    import colorcet as cc

    fig = figure(title=ftmsresults.name, tools=["pan", "box_zoom", "xwheel_zoom", "ywheel_zoom", "wheel_zoom", "save", "reset"])

    fig.xaxis.axis_label = "m/z"
    fig.yaxis.axis_label = "Abundance"

    # fig.line(x=ftmsresults.mz_raw, y=ftmsresults.abun_raw, line_color="black",
    #         line_width=1, line_alpha=0.5, legend_label='All Peaks')

    unassigned_df = df[df['Heteroatom Class'] == 'unassigned']

    assigned_df = df[df['Heteroatom Class'] != 'unassigned']

    fig.segment(x0=unassigned_df['m/z'], x1=unassigned_df['m/z'],
                    y0=np.zeros(len(unassigned_df)), y1=unassigned_df['Peak Height'],
                    line_width=1.5, line_color='red', alpha=1.0, legend_label='Unassigned')

    fig.segment(x0=assigned_df['m/z'], x1=assigned_df['m/z'],
                    y0=np.zeros(len(assigned_df)), y1=assigned_df['Peak Height'],
                    line_width=1.5, line_color='black', alpha=1.0, legend_label='All Assigned')

    i = 0
    classes = natsorted(list(set(df['Heteroatom Class'])))
    classes_incl = []
    classes_excl = ['unassigned', '13C', '18O', '17O', '15N', '34S']
    for name in classes:
        if any(x in name for x in classes_excl):
            continue
        else:
            classes_incl.append(name)

    palette = cc.glasbey_light
    nitems = len(classes_incl)if len(classes_incl) > 0 else 1

    spacing = int(len(palette) / nitems) - 1
    if spacing < 1:
        spacing = 1  # If too many classes it will be 0, and throw an error.
    palette = palette[::spacing]  # support for dynamic number of classes up to 256.
    for name in classes_incl:
        class_data_df = df[df['Heteroatom Class'] == name]
        fig.segment(x0=class_data_df['m/z'], x1=class_data_df['m/z'],
                    y0=np.zeros(len(class_data_df)), y1=class_data_df['Peak Height'],
                    line_width=1.5, line_color=palette[i], alpha=1.0, legend_label=name)
        if i == 255:
            i = 0
        else:
            i = i + 1

    # this was for limiting the pan/zoom bounds but its problematic
    # fig.x_range = Range1d(min(ftmsresults.mz_raw)*0.9,max(ftmsresults.mz_raw)*1.1,bounds='auto')
    # fig.y_range = Range1d(min(ftmsresults.abun_raw)*0.9,max(ftmsresults.abun_raw)*1.1,bounds='auto')

    fig.toolbar.logo = None
    fig.toolbar_location = "above"

    fig.legend.location = "top_right"
    fig.legend.click_policy = "hide"
    fig.sizing_mode = "stretch_both"

    return fig

def generate_ftms_plots(ftmsresults) -> Tabs:

    df = ftmsresults.to_dataframe()
    source = ColumnDataSource(df)

    class_fig = class_plot(ftmsresults, df)
    error_fig = error_plot(ftmsresults, df)
    vank_fig = vankrevelen_plot(ftmsresults, df)

    columns = [
        TableColumn(field="m/z", title="m/z"),
        TableColumn(field="Calculated m/z", title="Calculated m/z"),
        TableColumn(field="Peak Height", title="Peak Height"),
        TableColumn(field="m/z Error (ppm)", title="m/z Error (ppm)"),
        TableColumn(field="m/z Error Score", title="m/z Error Score"),
        TableColumn(field="Isotopologue Similarity", title="Isotopologue Score"),
        TableColumn(field="Confidence Score", title="Confidence Score"),
        TableColumn(field="Molecular Formula", title="Molecular Formula"),
        TableColumn(field="Heteroatom Class", title="Heteroatom Class"),
        TableColumn(field="DBE", title="DBE"),
    ]

    data_table = DataTable(source=source, columns=columns, sizing_mode="stretch_both")
    tab1 = Panel(child=class_fig, title="Mass Spectrum")
    tab2 = Panel(child=error_fig, title="Error Plot")
    tab3 = Panel(child=vank_fig, title="Van Krevelen Plot")
    tab4 = Panel(child=data_table, title="Data Table")
    tabs = Tabs(tabs=[tab1, tab2, tab3, tab4], sizing_mode="stretch_both")
    tabs.height = 1200
    return tabs

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

    parameter_class = MSParameters()
    parameter_class.mass_spectrum = ms_settings
    parameter_class.ms_peak = mspeak_settings
    parameter_class.molecular_search = molformula_settings
    parameter_class.data_input = data_input_settings
    parameter_class.transient = transient_settings
    parameter_class.lc = lc_settings

    return parameter_class

def run_workflow(current_user, file_location, filetype, ref_calibration_file, parameters_id):

    parameters = query_parameters(current_user, parameters_id)

    first_scan = parameters.lc.start_scan
    last_scan = parameters.lc.final_scan

    if filetype == 'thermo_reduced_profile':

        from corems.mass_spectra.input import rawFileReader

        reader = rawFileReader.ImportMassSpectraThermoMSFileReader(file_location)
        mass_spectrum = reader.get_average_mass_spectrum_in_scan_range(first_scan, last_scan, auto_process=False)

    elif filetype == 'bruker_transient':

        with ReadBrukerSolarix(file_location) as transient:
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

    # store setting inside mass spectrum obj
    mass_spectrum.parameters = parameters
    if mass_spectrum.is_centroid:
        mass_spectrum.filter_by_noise_threshold()
    else:
        mass_spectrum.process_mass_spec()
    # force it to one job. daemon child can not have child process
    mass_spectrum.molecular_search_settings.db_jobs = 1

    if ref_calibration_file:

        MzDomainCalibration(mass_spectrum, ref_calibration_file).run()

    SearchMolecularFormulas(mass_spectrum, first_hit=False).run_worker_mass_spectrum()

    return mass_spectrum

def workflow_worker(current_user, file_class, ftmsresults, id_cal_file, parameters_id):

    reference_class = current_user.ftms_data.get(id_cal_file)

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

    db.session.flush()

def update_ftms_result(user_id, file_id, ftmsresult_id):

    current_user = User.query.get(user_id)

    # release session
    db.session.flush()

    # get class objs
    file_class = current_user.ftms_data.get(file_id)

    ftmsresults = current_user.ftms_results.get(ftmsresult_id)
    ftmsresults.status = 'Active'
    db.session.flush()

    return current_user, file_class, ftmsresults

@celery.task(bind=True, name='api.ftms_tasks.run_direct_infusion_workflow')
def run_direct_infusion_workflow(self, args):

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
        ftmsresults.stats = json.dumps({'error': str(exception)})

        return {'current': 100, 'total': 100, 'status': 'Task Failed!',
                'result': str(exception)}
