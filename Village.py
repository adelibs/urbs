import os
import pandas as pd
import pyomo.environ
import shutil
import urbs
from datetime import datetime
from pyomo.opt.base import SolverFactory


# SCENARIOS
def scenario_base(data):
    # do nothing
    return data

def prepare_result_directory(result_name):
    """ create a time stamped directory within the result folder """
    # timestamp for result directory
    now = datetime.now().strftime('%Y%m%dT%H%M')

    # create result directory if not existent
    result_dir = os.path.join('result', '{}-{}'.format(result_name, now))
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    return result_dir


def setup_solver(optim, logfile='solver.log'):
    """ """
    if optim.name == 'gurobi':
        # reference with list of option names
        # http://www.gurobi.com/documentation/5.6/reference-manual/parameters
        optim.set_options("logfile={}".format(logfile))
        # optim.set_options("timelimit=7200")  # seconds
        # optim.set_options("mipgap=5e-4")  # default = 1e-4
    elif optim.name == 'glpk':
        # reference with list of options
        # execute 'glpsol --help'
        optim.set_options("log={}".format(logfile))
        # optim.set_options("tmlim=7200")  # seconds
        # optim.set_options("mipgap=.0005")
    else:
        print("Warning from setup_solver: no options set for solver "
              "'{}'!".format(optim.name))
    return optim


def run_scenario(input_file, timesteps, scenario, result_dir, dt,
                 plot_tuples=None,  plot_sites_name=None, plot_periods=None,
                 report_tuples=None, report_sites_name=None):
    """ run an urbs model for given input, time steps and scenario

    Args:
        input_file: filename to an Excel spreadsheet for urbs.read_excel
        timesteps: a list of timesteps, e.g. range(0,8761)
        scenario: a scenario function that modifies the input data dict
        result_dir: directory name for result spreadsheet and plots
        dt: length of each time step (unit: hours)
        plot_tuples: (optional) list of plot tuples (c.f. urbs.result_figures)
        plot_sites_name: (optional) dict of names for sites in plot_tuples
        plot_periods: (optional) dict of plot periods(c.f. urbs.result_figures)
        report_tuples: (optional) list of (sit, com) tuples (c.f. urbs.report)
        report_sites_name: (optional) dict of names for sites in report_tuples

    Returns:
        the urbs model instance
    """

    # scenario name, read and modify data for scenario
    sce = scenario.__name__
    data = urbs.read_excel(input_file)
    data = scenario(data)
    urbs.validate_input(data)

    # create model
    prob = urbs.create_model(data, dt, timesteps)

    # refresh time stamp string and create filename for logfile
    now = prob.created
    log_filename = os.path.join(result_dir, '{}.log').format(sce)

    # solve model and read results
    optim = SolverFactory('gurobi', solver_io="python")  # cplex, glpk, gurobi, ...
    optim = setup_solver(optim, logfile=log_filename)
    result = optim.solve(prob, tee=True)

    # save problem solution (and input data) to HDF5 file
    #urbs.save(prob, os.path.join(result_dir, '{}.h5'.format(sce)))

    # write report to spreadsheet
    urbs.report(
        prob,
        os.path.join(result_dir, '{}.xlsx').format(sce),
        report_tuples=report_tuples,
        report_sites_name=report_sites_name)

    # result plots
    urbs.result_figures(
        prob,
        os.path.join(result_dir, '{}'.format(sce)),
        plot_title_prefix=sce.replace('_', ' '),
        plot_tuples=plot_tuples,
        plot_sites_name=plot_sites_name,
        periods=plot_periods,
        figure_size=(24, 9))
    return prob


if __name__ == '__main__':
    input_file = 'Village.xlsx'
    result_name = os.path.splitext(input_file)[0]  # cut away file extension
    result_dir = prepare_result_directory(result_name)  # name + time stamp

    # copy input file to result directory
    shutil.copyfile(input_file, os.path.join(result_dir, input_file))
    # copy runme.py to result directory
    shutil.copy(__file__, result_dir)

    # simulation timesteps
    (offset, length) = (2000,2500)  # time step selection
    timesteps = range(offset, offset+length+1)
    dt = 1  # length of each time step (unit: hours)

    # plotting commodities/sites
    plot_tuples = [
        ('Village', 'Elec'),
       #('Village', 'Diesel'), 
       #('Village', 'Solar'),
       #('Village', 'Domestic Water'),
       ('Village', 'Groundwater'),
       ('Village', 'Irrigation Water'),
       ('Village', 'Maize'),
       ('Village', 'Maize Stover'),
       #('Village', 'Substrate'),
       #('Village', 'Methan'),
       #('Village', 'Manure'),
       #('Village', 'MaizeBuy'),
       ('Village', 'Soil Water'),
       ('Village', 'Blue Water'),
       #('Village', 'EffRain'),
       ('Village', 'Green Water'),
       # ('Village', 'Wheat Waste'),
       # ('Village', 'WheatSell'),
       # ('Village', 'Biogas Equivalent'),
       # ('Village', 'Biogas'),
       # ('Village', 'Rain'),
        ]

    # optional: define names for sites in plot_tuples
    plot_sites_name = {}

    # detailed reporting commodity/sites
    report_tuples = [
        ('Village', 'Elec'),
       #('Village', 'Diesel'), 
       #('Village', 'Solar'),
       #('Village', 'Domestic Water'),
       ('Village', 'Groundwater'),
       ('Village', 'Irrigation Water'),
       ('Village', 'Maize'),
       ('Village', 'Maize Stover'),
       #('Village', 'Substrate'),
       #('Village', 'Methan'),
       #('Village', 'Manure'),
       #('Village', 'MaizeBuy'),
       ('Village', 'Blue Water'),
       ('Village', 'EffRain'),
       ('Village', 'Soil Water'),
       ('Village', 'Green Water'),
       # ('Village', 'Wheat Waste'),
       # ('Village', 'WheatSell'),
       # ('Village', 'Biogas Equivalent'),
       # ('Village', 'Biogas'),
       # ('Village', 'Rain'),
        ]
 
    # optional: define names for sites in report_tuples
    report_sites_name = {}

    # plotting timesteps
    plot_periods = {
       'all': timesteps[1:],
       #'January': range(   1,  336),
       #'January2': range(   337,  600),
       #'January3': range(  601, 1000),
       #'March': range(1401,  1776),
       'April': range(2161,  2496),
       #'July': range( 4321,  4656),
       #'September': range(5761,  6096),
       #'November': range( 7201,  7536),
       #'all_1': range( 1,  4320),
       #'all_2': range( 4321,  8760),
       #'1_day': range(   1,  24),
       #'1_week': range(   1,  168),
       #'1_month': range(   1,  672),
        }

    # add or change plot colors
    my_colors = {
        'Demand': (0, 0, 0),
        'Diesel Generator': (187, 187, 187),
        'Photovoltaics': (255,201,71),
        'WaterBuy to Domestic Water':(200,221,241),
        'Groundwater to Blue Water':(4,131,255),
        'Soil Water to Irrigation Water':(193,229,241),
        'Groundwater to Domestic Water':(152,245,255),
        'MaizeBuy to Maize':(205,170,125),
        #'Biogas Generator':(172,233,110),
        #'Biogas Digester':(54,93,14),    
        'Maize Farm':(245,222,179),
        'Water Pump':(91, 155, 213),
        'Green Water to Soil Water':(155,205,155),
        'Shunt(Green Water)':(34,139,34),
        'EffRain to Green Water':(81,102,45),
        #'Shunt(Waste)':(95,66,55),
        #'Wheat to WheatSell':(140,111,62),
        #'Wheat Waste to Biogas Equivalent':(173,130,114),
        #'Wheat to Biogas Equivalent':(173,154,160),
        #'Rain to Irrigation Water':(119,143,252),
        }
    for country, color in my_colors.items():
        urbs.COLORS[country] = color

    # select scenarios to be run
    scenarios = [
        scenario_base,
        #scenario_stock_prices,
        #scenario_co2_limit,
        #scenario_co2_tax_mid,
        #scenario_no_dsm,
        #scenario_north_process_caps,
        #scenario_all_together
        ]

    for scenario in scenarios:
        prob = run_scenario(input_file, timesteps, scenario, result_dir, dt,
                            plot_tuples=plot_tuples,
                            plot_sites_name=plot_sites_name,
                            plot_periods=plot_periods,
                            report_tuples=report_tuples,
                            report_sites_name=report_sites_name,
                            )
