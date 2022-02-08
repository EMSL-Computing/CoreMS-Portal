

from multiprocessing import Pool

from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, TapTool, HoverTool, Slider, DataTable, CustomJS, TableColumn, IndexFilter, CDSView
from bokeh.plotting import figure
from bokeh.layouts import column
from bokeh.palettes import turbo
import bokeh.models as bmo

from flask_login import current_user
from s3path import S3Path
from pandas import DataFrame
import numpy as np

from corems.mass_spectra.input.andiNetCDF import ReadAndiNetCDF

# from app.workflows.gcms.bokeh_utils import plot_styler
from app.workflows.gcms.gcms_workflow import query_parameters


def run_workflow(file_id):

    parameters = current_user.gcms_parameters.filter_by(name='default').first()

    parameter_class = query_parameters(current_user, parameters.id)

    parameter_class.gc_ms.use_deconvolution = False

    file_class = current_user.gcms_data.filter_by(id=file_id).first()

    filepath = file_class.filepath

    file_s3path = S3Path('/gcms-data/' + filepath)

    reader_gcms = ReadAndiNetCDF(file_s3path)

    reader_gcms.run()

    gcms = reader_gcms.get_gcms_obj()

    gcms.parameter = parameter_class

    gcms.process_chromatogram()

    return gcms

def generate_gcms_plots(gcms):

    df = gcms.to_dataframe()
    source = ColumnDataSource(df)

    ms_fig, ms_slider, ms_filters, ms_source, ms_start_end_index = plot_mass_spectra(gcms)
    chorma_fig = gcms_plot(gcms, source, ms_filters, ms_source, ms_start_end_index, ms_slider)

    gcms_layout = column(
        chorma_fig,
        ms_slider,
        ms_fig,
    )
    gcms_layout.sizing_mode = "stretch_both"

    columns = [
        TableColumn(field='Retention Time', title='Retention Time'),
        TableColumn(field='Peak Height', title='Peak Height'),
    ]

    data_table = DataTable(source=source, columns=columns, sizing_mode="stretch_both")

    tab1 = Panel(child=gcms_layout, title="Chromatogram")
    tab2 = Panel(child=data_table, title="Data Table")
    tabs = Tabs(tabs=[tab1, tab2], sizing_mode="stretch_both")
    tabs.height = 1200

    return tabs

def plot_mass_spectra(gcms):

    mz_abu = {'mz': [], 'abundance': [], 'zeros': []}

    first_len = (len(gcms[0].mass_spectrum.mz_exp))
    start_end_index = []

    amp_slider = Slider(start=0, end=len(gcms) - 1, value=0, step=1, title="MassSpectrum")

    for gcms_peak in gcms:

        start_index = len(mz_abu.get('mz'))

        len_data = len(gcms_peak.mass_spectrum.abundance)

        mz_abu.get('mz').extend(gcms_peak.mass_spectrum.mz_exp)
        mz_abu.get('abundance').extend(gcms_peak.mass_spectrum.abundance)
        mz_abu.get('zeros').extend(np.zeros(len_data))

        final_index = len(mz_abu.get('mz')) - 1

        start_end_index.append((start_index, final_index))
        print(start_index, final_index, len_data)

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

    callback = CustomJS(args=dict(source=source, start_end_index=start_end_index, filter=filters, amp=amp_slider, ),
                        code="""

        function* range(start, end) {
        for (let i = start; i <= end; i++) {
            yield i;
            }
        }

        let start = start_end_index[amp.value][0];
        let end = start_end_index[amp.value][1];

        filter.indices = [...range(start, end)]
        source.change.emit()

    """)
    amp_slider.js_on_change('value', callback)

    fig = figure(tools=["pan", "box_zoom", hover_tool, "xwheel_zoom", "wheel_zoom", "save", "reset"])
    fig.segment(x0='mz', x1='mz', y0='abundance', y1='zeros', name='massSpectrum', source=source, line_color="black", line_width=2, line_alpha=0.7, view=view)

    fig.xaxis.axis_label = "m/z"
    fig.yaxis.axis_label = "Ion Current"
    fig.toolbar.logo = None
    fig.toolbar_location = "above"
    fig.sizing_mode = "stretch_both"
    # plot_styler(fig)

    return fig, amp_slider, filters, source, start_end_index

def gcms_plot(gcms, source, ms_filters, ms_source, ms_start_end_index, ms_slider) -> figure:

    from bokeh.palettes import Spectral10

    fig = figure(title=gcms.sample_name, tools=["pan", "box_zoom", "xwheel_zoom", "wheel_zoom", "save", "reset"])

    hover_tool = HoverTool(names=['peaks'], tooltips=[
        ('Index', '@{Peak Index}'),
        ("Retention Time", "@{Retention Time}{0.000}"),
        ("Peak Height", "@{Peak Height}{0.0000}"),

    ],
        formatters={
            '@date': 'datetime',        # use 'datetime' formatter for '@date' field
            '@{adj close}': 'printf',   # use 'printf' formatter for '@{adj close}' field
                                        # use default 'numeral' formatter for other fields
    },
        # display a tooltip whenever the cursor is vertically in line with a glyph
        mode='vline')

    circle = fig.circle(x='Retention Time', y='Peak Height', size=8, source=source, color='red', name='peaks')

    callback = CustomJS(args=dict(circle=circle.data_source, start_end_index=ms_start_end_index, filter=ms_filters, source=ms_source, ms_slider=ms_slider), code="""
    // the event that triggered the callback is cb_obj:
    // The event type determines the relevant attributes
    let sel_index = circle.selected.indices[0]
    function* range(start, end) {
        for (let i = start; i <= end; i++) {
            yield i;
            }
        }
        ms_slider.value = sel_index;
        let start = start_end_index[sel_index][0];
        let end = start_end_index[sel_index][1];

        filter.indices = [...range(start, end)]
        source.change.emit()
    """)
    taptool = TapTool(callback=callback, renderers=[circle])
    fig.line(x=gcms.retention_time, y=gcms.tic, line_color="black", line_width=2, line_alpha=0.7)

    fig.add_tools(taptool, hover_tool)

    fig.xaxis.axis_label = "Retention Time (min)"
    fig.yaxis.axis_label = "Total Ion Current"
    fig.toolbar.logo = None
    fig.toolbar_location = "above"
    fig.sizing_mode = "stretch_both"
    
    # plot_styler(fig)
    return fig

def run_load_gcms_data(id_data):

    worker_args = [id_data]

    cores = 1
    pool = Pool(cores)

    ms_results = []
    gcms = pool.map(run_workflow, worker_args)

    pool.close()
    pool.join()

    tabs = generate_gcms_plots(gcms[0])

    return tabs
    # return ms_results
