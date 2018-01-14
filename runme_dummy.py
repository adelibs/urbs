import os
import pandas as pd
import pyomo.environ
import shutil
import urbs
from datetime import datetime
from pyomo.opt.base import SolverFactory


# SCENARIOS
def scenario_base(data):
    #sto = data['storage']
    #sto.loc[('StRupertMayer', 'Battery'), 'cap-up-c'] = 0
    #sto.loc[('StRupertMayer', 'Biogas Storage'), 'cap-up-c'] = 0
    #sto.loc[('StRupertMayer', 'Silo'), 'cap-up-c'] = 0
    #pro = data['process']
    #pro.loc[('StRupertMayer', 'Photovoltaics'), 'cap-up'] = 0
    #pro.loc[('StRupertMayer', 'Diesel Generator'), 'cap-up']=0
    
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


def run_scenario(input_file, timesteps, scenario, result_dir,
                 plot_tuples=None, plot_periods=None, report_tuples=None):
    """ run an urbs model for given input, time steps and scenario

    Args:
        input_file: filename to an Excel spreadsheet for urbs.read_excel
        timesteps: a list of timesteps, e.g. range(0,8761)
        scenario: a scenario function that modifies the input data dict
        result_dir: directory name for result spreadsheet and plots
        plot_tuples: (optional) list of plot tuples (c.f. urbs.result_figures)
        plot_periods: (optional) dict of plot periods (c.f. urbs.result_figures)
        report_tuples: (optional) list of (sit, com) tuples (c.f. urbs.report)

    Returns:
        the urbs model instance
    """

    # scenario name, read and modify data for scenario
    sce = scenario.__name__
    data = urbs.read_excel(input_file)
    data = scenario(data)

    # create model
    prob = urbs.create_model(data, timesteps)

    # refresh time stamp string and create filename for logfile
    now = prob.created
    log_filename = os.path.join(result_dir, '{}.log').format(sce)

    # solve model and read results
    optim = SolverFactory('gurobi', solver_io="python")  # cplex, glpk, gurobi, ...
    optim = setup_solver(optim, logfile=log_filename)
    result = optim.solve(prob, tee=True)

    # save problem solution (and input data) to HDF5 file
   # urbs.save(prob, os.path.join(result_dir, '{}.h5'.format(sce)))

    # write report to spreadsheet
    urbs.report(
        prob,
        os.path.join(result_dir, '{}.xlsx').format(sce),
        report_tuples=report_tuples)

    # result plots
    urbs.result_figures(
        prob,
        os.path.join(result_dir, '{}'.format(sce)),
        plot_title_prefix=sce.replace('_', ' '),
        plot_tuples=plot_tuples,
        periods=plot_periods,
        figure_size=(24, 9))
    return prob

if __name__ == '__main__':
    input_file = 'dummy_D_PV_Bio_Field_Water_Sell.xlsx'
    result_name = os.path.splitext(input_file)[0]  # cut away file extension
    result_dir = prepare_result_directory(result_name)  # name + time stamp

    # copy input file to result directory
    shutil.copyfile(input_file, os.path.join(result_dir, input_file))
    # copy runme.py to result directory
    shutil.copyfile(__file__, os.path.join(result_dir, 'runme_dummy.py'))

    # simulation timesteps
    (offset, length) = (0,100)  # time step selection
    timesteps = range(offset, offset+length+1)

    # plotting commodities/sites
    plot_tuples = [
       ('StRupertMayer', 'Elec'),
       ('StRupertMayer', 'Diesel'), 
       ('StRupertMayer', 'Solar'),
       ('StRupertMayer', 'Biogas'),
       ('StRupertMayer', 'Tomato'),
       ('StRupertMayer', 'Water'),
       #('StRupertMayer', 'Tomato Sell'),
       ]
    
    # detailed reporting commodity/sites
    report_tuples = [
       ('StRupertMayer', 'Elec'),
       ('StRupertMayer', 'Diesel'),        
       ('StRupertMayer', 'Solar'),  
       ('StRupertMayer', 'Biogas'),
       ('StRupertMayer', 'Tomato'),
       ('StRupertMayer', 'Water'),
       #('StRupertMayer', 'Tomato Sell'),
       ]

    # plotting timesteps
    plot_periods = {
       # 'all': timesteps[1:168],
       '1_week': range(   1,  168),
        #'1_day': range(   1,  24),
       '1_month': range(   1,  672),
        }

    # add or change plot colors
    my_colors = {
        'Demand': (0, 0, 0),
        'Diesel Generator': (89, 89, 89),
        'Photovoltaics': (255,201,71),
        #'Battery':(200, 230, 200),
        'Biogas Generator':(172,233,110),
        'Biomass Digester':(54,93,14),    
        'Tomato Field':(213,91,94),
        'Water Pump':(91, 155, 213),
        'Feed-in Tomato':(101,26,28),
        }
    for country, color in my_colors.items():
        urbs.COLORS[country] = color

    # select scenarios to be run
    scenarios = [
        scenario_base,
     ]

    for scenario in scenarios:
        prob = run_scenario(input_file, timesteps, scenario, result_dir,
                            plot_tuples=plot_tuples,
                            plot_periods=plot_periods,
                            report_tuples=report_tuples)