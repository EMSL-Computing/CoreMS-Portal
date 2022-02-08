from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path
import json

from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, CustomJS, Select, TapTool, Slider, HoverTool, DataTable, TableColumn, IndexFilter, CDSView
from bokeh.plotting import figure
from bokeh.layouts import column, row

from corems.mass_spectra.input.andiNetCDF import ReadAndiNetCDF
from corems.encapsulation.input import parameter_from_json
from corems.mass_spectra.calc.GC_RI_Calibration import get_rt_ri_pairs
from corems.molecular_id.search.compoundSearch import LowResMassSpectralMatch
from corems.encapsulation.factory.processingSetting import CompoundSearchSettings, GasChromatographSetting
from corems.encapsulation.factory.parameters import GCMSParameters

import numpy as np
from pandas import DataFrame

from app import db
from app import celery
from app.models.auth_models import User
# from app.workflows.gcms.bokeh_utils import plot_styler
from app.config import Config
from s3path import S3Path

def normalize(list_data):

    data_array = np.array(list_data)
    max_data = data_array.max()
    normalized_array = (data_array / max_data) * 100
    return normalized_array.tolist()

def mass_spec_plot(gcms_results):

    gcpeaks_rt_list = gcms_results.peaks_to_dict()
    mz_abu = {'mz': [], 'abundance': [], 'zeros': []}

    first_key = list(gcpeaks_rt_list.get('peak_data').keys())[0]
    first_len = len(gcpeaks_rt_list.get('peak_data')[first_key].get('mz'))

    start_end_index = []
    index_candidates_options = []
    # print(gcms_results.peaks_to_dict())
    for gcms_peak_rt in gcpeaks_rt_list.get('peak_data').keys():

        gcms_peak = gcpeaks_rt_list.get('peak_data').get(gcms_peak_rt)

        start_index = len(mz_abu.get('mz'))
        len_data = len(gcms_peak.get('mz'))

        mz_abu.get('mz').extend(gcms_peak.get('mz'))

        mz_abu.get('abundance').extend(normalize(gcms_peak.get('abundance')))
        mz_abu.get('zeros').extend(np.zeros(len_data))

        final_index = len(mz_abu.get('mz')) - 1

        start_end_index.append((start_index, final_index))

        index_candidates_options.append(gcms_peak.get('candidate_names'))

    # {0: ['foo', "bar"], 1: ["bar"]}
    ms_df = DataFrame(mz_abu)
    source = ColumnDataSource(ms_df)
    filters = IndexFilter(list(range(first_len)))
    view = CDSView(source=source, filters=[filters])

    hover_tool = HoverTool(names=['massSpectrum'], tooltips=[
        ("m/z", "@{mz}{0}"),
        ("Peak Height", "@{abundance}{0.00}"),

    ],
        formatters={
            '@date': 'datetime',        # use 'datetime' formatter for '@date' field
            '@{adj close}': 'printf',   # use 'printf' formatter for '@{adj close}' field
                                        # use default 'numeral' formatter for other fields
    },
        # display a tooltip whenever the cursor is vertically in line with a glyph
        mode='vline')

    fig = figure(tools=["pan", "box_zoom", hover_tool, "xwheel_zoom", "wheel_zoom", "save", "reset"])

    first_candidates = gcpeaks_rt_list.get('peak_data')[first_key].get('candidate_names')

    if first_candidates:

        first_candidate = first_candidates[0]

    else:

        first_candidate = 'None'

    candidates_data = gcpeaks_rt_list.get('ref_data')
    candidate_data = candidates_data.get(first_candidate)

    if candidate_data:

        candidate_data['abundance'] = normalize(candidate_data.get('abundance'))
        candidate_data['zeros'] = np.zeros(len(candidate_data.get('mz'))).tolist()

    else:

        candidate_data = {}
        candidate_data['mz'] = []
        candidate_data['abundance'] = []
        candidate_data['zeros'] = []

    candidate_sources_df = DataFrame(candidate_data)
    candidate_sources_df['abundance'] = candidate_sources_df['abundance'] * -1
    candidate_source = ColumnDataSource(candidate_sources_df)

    fig.segment(x0='mz', x1='mz', y0='abundance', y1='zeros', source=candidate_source, line_color="red", line_width=2, line_alpha=0.7)

    select = Select(title="Candidate:", value=first_candidate, options=first_candidates)
    select.js_on_change("value", CustomJS(args=dict(candidate_source=candidate_source, candidates_data=candidates_data), code="""

        function normalize(inArray) {
            const max_abun = Math.max(...inArray);
            const map1 = inArray.map(x => (x / max_abun)* -100);
            return map1;
        }

        let current_candidate = this.value;

        if (candidates_data[current_candidate]){
            var new_data = {"mz": candidates_data[current_candidate]['mz'],
                            "abundance": normalize(candidates_data[current_candidate]['abundance']) ,
                            "zeros" :  new Array(candidates_data[current_candidate]['mz'].length+1).join('0').split('').map(parseFloat) };

        }else{

             var new_data = {"mz": [],
                            "abundance": [],
                            "zeros" : [] };

        };
        candidate_source.data = new_data;
        candidate_source.change.emit();
        """))

    amp_slider = Slider(start=0, end=len(gcpeaks_rt_list.get('peak_data')) - 1, value=0, step=1, title="MassSpectrum")

    callback = CustomJS(args=dict(source=source, start_end_index=start_end_index,
                                    filter=filters, amp=amp_slider, cand_select=select,
                                    index_candidates_options=index_candidates_options,
                                    candidate_source=candidate_source,
                                    candidates_data=candidates_data
                                  ),
                        code="""

        function* range(start, end) {
        for (let i = start; i <= end; i++) {
            yield i;
            }
        }

        function normalize(inArray) {
            const max_abun = Math.max(...inArray)
            const map1 = inArray.map(x => (x / max_abun)* -100);
            return map1;
        }


        let start = start_end_index[amp.value][0];
        let end = start_end_index[amp.value][1];
        cand_select.options = index_candidates_options[amp.value];
        filter.indices = [...range(start, end)];

        let current_candidate = index_candidates_options[amp.value][0];

        if (candidates_data[current_candidate]){
            var new_data = {"mz": candidates_data[current_candidate]['mz'],
                            "abundance": normalize(candidates_data[current_candidate]['abundance']) ,
                            "zeros" :  new Array(candidates_data[current_candidate]['mz'].length+1).join('0').split('').map(parseFloat) };


        }else{

             var new_data = {"mz": [],
                            "abundance": [],
                            "zeros" : [] };

        };

        candidate_source.data = new_data;
        candidate_source.change.emit();
        source.change.emit();

    """)

    amp_slider.js_on_change('value', callback)

    fig.segment(x0='mz', x1='mz', y0='abundance', y1='zeros', name='massSpectrum', source=source, line_color="black", line_width=2, line_alpha=0.7, view=view)

    fig.xaxis.axis_label = "m/z"
    fig.yaxis.axis_label = "Ion Current"
    fig.toolbar.logo = None
    fig.toolbar_location = "above"
    fig.sizing_mode = "stretch_both"

    # plot_styler(fig)

    return fig, amp_slider, filters, source, start_end_index, select, index_candidates_options, candidate_source, candidates_data

def chromatogram_plot(gcms_results, df, ms_filters, ms_source, ms_start_end_index, candidate_selection,
                        index_candidates_options, candidate_source, candidates_data, ms_slider) -> figure:
    import colorcet as cc

    # grouped_df = df.groupby("Retention Time").max(level='Similarity Score')
    idx_assigned = df.groupby(['Retention Time'])['Similarity Score'].transform(max) == df['Similarity Score']

    idx_not_assigned = df['Similarity Score'].isna()
    df_not_assigned = df[idx_not_assigned]

    maximums_df = df[idx_assigned]

    all_rows = maximums_df.append(df_not_assigned, ignore_index=True)

    sorted_all_rows = all_rows.sort_values(by=['Retention Time'])
    # maximums = grouped_df.reset_index()

    source = ColumnDataSource(sorted_all_rows.reset_index())

    hover_tool = HoverTool(names=['peaks'], tooltips=[

        ('Peak Index', '@{Peak Index}'),
        ('Retention Time', '@{Retention Time}{0.0000}'),
        ('Retention Time Ref', '@{Retention Time Ref}{0.0000}'),
        ('Retention index', '@{Retention index}{0.0000}'),
        ('Retention index Ref', '@{Retention index Ref}{0.0000}'),
        ('Spectral Similarity Score', '@{Spectral Similarity Score}{0.000}'),
        ('Similarity Score', '@{Similarity Score}{0.000}'),
        ('Compound Name', '@{Compound Name}'),
    ],
        formatters={
            '@date': 'datetime',        # use 'datetime' formatter for '@date' field
            '@{adj close}': 'printf',   # use 'printf' formatter for '@{adj close}' field
                                        # use default 'numeral' formatter for other fields
    },
        # display a tooltip whenever the cursor is vertically in line with a glyph
        mode='vline')

    fig = figure(title=gcms_results.name, tools=['pan', 'box_zoom', 'xwheel_zoom', 'ywheel_zoom', 'wheel_zoom', 'save', 'reset', hover_tool])

    circle = fig.circle(x='Retention Time', y='Peak Height', size=10, source=source, color='red', name='peaks')
    fig.line(x=gcms_results.rt, y=gcms_results.tic, line_color='black', line_width=3, line_alpha=0.8)

    callback = CustomJS(args=dict(circle=circle.data_source, start_end_index=ms_start_end_index,
                                    filter=ms_filters, source=ms_source, cand_select=candidate_selection,
                                    index_candidates_options=index_candidates_options,
                                    candidate_source=candidate_source,
                                    candidates_data=candidates_data,
                                    ms_slider=ms_slider), code="""
    // the event that triggered the callback is cb_obj:
    // The event type determines the relevant attributes
        let sel_index = circle.selected.indices[0]
        function* range(start, end) {
            for (let i = start; i <= end; i++) {
                yield i;
                }
            }

        function normalize(inArray) {
            const max_abun = Math.max(...inArray)
            const map1 = inArray.map(x => (x / max_abun)*-100);
            return map1;
        }
        ms_slider.value = sel_index;

        let start = start_end_index[sel_index][0];
        let end = start_end_index[sel_index][1];
        filter.indices = [...range(start, end)];

        cand_select.options = index_candidates_options[sel_index];

        let current_candidate = index_candidates_options[sel_index][0];
        if (candidates_data[current_candidate]){
            var new_data = {"mz": candidates_data[current_candidate]['mz'],
                            "abundance": normalize(candidates_data[current_candidate]['abundance']),
                            "zeros" :  new Array(candidates_data[current_candidate]['mz'].length+1).join('0').split('').map(parseFloat) };

        }else{

             var new_data = {"mz": [],
                            "abundance": [],
                            "zeros" : [] };

        };

        candidate_source.data = new_data;
        candidate_source.change.emit();

        source.change.emit();
    """)

    taptool = TapTool(callback=callback, renderers=[circle])
    fig.add_tools(taptool, hover_tool)
    if gcms_results.deconvolved:

        # print(gcms_results.peaks_to_dict())
        gcpeaks_rt_list = gcms_results.peaks_to_dict().get('peak_data')

        i = 0
        palette = cc.glasbey_light
        peaks_len = len(gcpeaks_rt_list.keys())
        spacing = int(len(palette) / peaks_len) - 1

        if spacing < 1:
            spacing = 1  # If too many classes it will be 0, and throw an error.
        palette = palette[::spacing]  # support for dynamic number of classes up to 256.

        for gcms_peak_rt in sorted(gcpeaks_rt_list.keys()):

            gcms_peak = gcpeaks_rt_list.get(gcms_peak_rt)
            fig.line(x=gcms_peak.get('rt'), y=gcms_peak.get('tic'), line_color=palette[i], line_width=2, line_alpha=0.8)

            if i == 255:
                i = 0
            else:
                i = i + 1

    fig.xaxis.axis_label = 'Retention Time'
    fig.yaxis.axis_label = 'Total Ion Chromatogram'
    fig.toolbar.logo = None
    fig.toolbar_location = "above"

    # plot_styler(fig)
    fig.sizing_mode = 'stretch_both'

    return fig

def datatable_gui(df) -> DataTable:

    source = ColumnDataSource(df)

    columns = [
        TableColumn(field='Retention Time', title='Retention Time'),
        TableColumn(field='Retention Time Ref', title='Retention Time Ref'),
        TableColumn(field='Retention index', title='Retention index'),
        TableColumn(field='Retention index Ref', title='Retention index Ref'),
        TableColumn(field='Spectral Similarity Score', title='Spectral Similarity Score'),
        TableColumn(field='Similarity Score', title='Similarity Score'),
        TableColumn(field='Compound Name', title='Compound Name'),
    ]

    data_table = DataTable(source=source, columns=columns)
    data_table.sizing_mode = 'stretch_both'

    return data_table

def generate_gcms_plots(gcms_results) -> Tabs:

    df = gcms_results.to_dataframe()

    ms_fig, ms_slider, ms_filters, ms_source, ms_start_end_index, candidate_selection, dict_index_candidates_options, candidate_source, candidates_data = mass_spec_plot(gcms_results)
    chroma_plot_fig = chromatogram_plot(gcms_results, df, ms_filters, ms_source,
                                        ms_start_end_index, candidate_selection, dict_index_candidates_options, candidate_source, candidates_data, ms_slider)
    data_table = datatable_gui(df)

    # options_layout.sizing_mode = "stretch_width"
    ms_slider.sizing_mode = "stretch_both"
    options = row(ms_slider, candidate_selection)

    options_layout = column(chroma_plot_fig, options, ms_fig)
    # gcms_layout.sizing_mode = "stretch_both"
    # ms_layout.sizing_mode = "stretch_both"
    options_layout.sizing_mode = "stretch_both"

    tab1 = Panel(child=options_layout, title='Plot')
    tab2 = Panel(child=data_table, title='Data Table')
    tabs = Tabs(tabs=[tab1, tab2])
    tabs.sizing_mode = 'stretch_both'
    tabs.max_height = 1200

    return tabs

def query_parameters(current_user, parameters_id) -> GCMSParameters:

    gcms_parameters = current_user.gcms_parameters.filter_by(id=parameters_id).first()

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

@celery.task(bind=True, name='api.gcms_tasks.run_gcms_metabolomics_workflow')
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

        db.session.flush()

        return {'current': 100, 'total': 100, 'status': 'Task completed!',
                'result': str(exception)}

def update_gcms_result(user_id, file_id, cal_file_id, gcms_result_id):

    current_user = User.query.get(user_id)

    # release session
    db.session.flush()

    # get class objs
    file_class = current_user.gcms_data.filter_by(id=file_id).first()
    cal_file_class = current_user.gcms_data.filter_by(id=cal_file_id).first()

    gcms_results = current_user.gcms_results.filter_by(id=gcms_result_id).first()
    gcms_results.status = 'Active'
    db.session.flush()

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
    db.session.flush()
