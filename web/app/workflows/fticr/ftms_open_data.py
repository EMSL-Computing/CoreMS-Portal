

from multiprocessing import Pool


from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, HoverTool, DataTable, TableColumn
from bokeh.plotting import figure
from bokeh.layouts import column
from bokeh.palettes import turbo
import bokeh.models as bmo

from corems.mass_spectrum.input.massList import ReadMassList
from corems.transient.input.brukerSolarix import ReadBrukerSolarix
from flask_login import current_user
from s3path import S3Path

from app.workflows.fticr.fticrms_workflow import query_parameters


def workflow_worker(params):

    
    file_id, param_id = params
     

    file_class = current_user.ftms_data.filter_by(id=file_id).first()

    filepath = file_class.filepath

    filetype = file_class.filetype

    s3path = S3Path('/fticr-data/' + filepath)

    mass_spec = run_workflow(s3path, filetype, param_id)

    return mass_spec

def run_workflow(file_location, filetype, param_id):

    parameters = current_user.ftms_parameters.filter_by(id=param_id).first()

    parameters = query_parameters(current_user, parameters.id)

    first_scan = int(parameters.lc.start_scan)
    last_scan = int(parameters.lc.final_scan)

    if filetype == 'thermo_reduced_profile':

        from corems.mass_spectra.input import rawFileReader

        reader = rawFileReader.ImportMassSpectraThermoMSFileReader(file_location)
        mass_spectrum = reader.get_average_mass_spectrum_in_scan_range(first_scan, last_scan)

    elif filetype == 'bruker_transient':

        with ReadBrukerSolarix(file_location) as transient:
            transient.parameters = parameters.transient
            mass_spectrum = transient.get_mass_spectrum(plot_result=False, auto_process=True)

    elif filetype == 'centroid_masslist':

        reader = ReadMassList(file_location)

        reader.parameters = parameters.data_input
        mass_spectrum = reader.get_mass_spectrum(parameters.molecular_search.ion_charge)

    elif filetype == 'profile_masslist':

        reader = ReadMassList(file_location)

        reader.parameters = parameters.data_input
        mass_spectrum = reader.get_mass_spectrum(parameters.molecular_search.ion_charge)


    # store setting inside mass spectrum obj
    mass_spectrum.parameters = parameters
    # force it to one job. daemon child can not have child process

    return mass_spectrum

def generate_ftms_plots(mass_spectrum):

    class_fig = ms_plot(mass_spectrum)

    df = mass_spectrum.to_dataframe()
    source = ColumnDataSource(df)

    columns = [
        TableColumn(field="m/z", title="m/z"),
        TableColumn(field="Calculated m/z", title="Calculated m/z"),
        TableColumn(field="Peak Height", title="Peak Height"),
        TableColumn(field="Resolving Power", title="Resolving Power"),
        TableColumn(field="S/N", title="S/N"),
    ]

    data_table = DataTable(source=source, columns=columns, sizing_mode="stretch_both")
    tab1 = Panel(child=class_fig, title="Mass Spectrum")
    tab2 = Panel(child=data_table, title="Data Table")
    tabs = Tabs(tabs=[tab1, tab2], sizing_mode="stretch_both")
    tabs.height = 1200
    return tabs

def ms_plot(mass_spectrum) -> figure:

    from bokeh.palettes import Spectral10

    min_max_mz, threshold = mass_spectrum.get_noise_threshold()
    baselise_noise = (mass_spectrum.baselise_noise, mass_spectrum.baselise_noise)

    fig = figure(title=mass_spectrum.sample_name, tools=["pan", "box_zoom", "wheel_zoom", "save", "reset"])

    fig.xaxis.axis_label = "m/z"
    fig.yaxis.axis_label = "Abundance"

    fig.line(x=mass_spectrum.mz_exp_profile, y=mass_spectrum.abundance_profile, line_color="black",
             line_width=1, line_alpha=0.5, legend_label='Mass Spectrum')

    fig.line(x=min_max_mz, y=threshold, line_color="red", line_width=2, line_alpha=1, legend_label='Noise Threshold')
    fig.line(x=min_max_mz, y=baselise_noise, line_color="yellow", line_width=2, line_alpha=1, legend_label='Noise Baseline')

    fig.legend.location = "top_right"
    fig.legend.click_policy = "hide"
    fig.toolbar.logo = None
    fig.toolbar_location = "above"
    fig.sizing_mode = "stretch_both"

    return fig

def run_load_data(id_data, param_id):

    worker_args = (id_data, param_id)
    
    cores = 1
    pool = Pool(cores)

    ms_results = []
    mass_spec = pool.map(workflow_worker, [worker_args])

    pool.close()
    pool.join()

    tabs = generate_ftms_plots(mass_spec[0])

    return tabs
    # return ms_results
