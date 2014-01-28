from flask import render_template, flash, redirect, request, make_response
from app import app
from app import Web_UI
import zipfile


EXPERIMENT = None
FILE_ID = 0
CUT = None

DEFAULT_PLOT_VALUE = {
    'Counts': ["Number of Stress Garnules per cell", "Conditions", "Number of Stress Granule per cell"],
    'Nuclear_Mean_Int': ["Nucleus Mean Intensity distribution", "Conditions", "Mean Intensity"],
    'Nuclear_Mean_Std': ["Nucleus Intensity Standard Deviation distribution", "Conditions", "Standard Deviation"],
    'Cytoplasm_Mean_Int': ["Cytoplasm Mean Intensity distribution", "Conditions", "Mean Intensity"],
    'Cytoplasm_Mean_Std': ["Cytoplasm Intensity Standard Deviation distribution", "Conditions", "Standard Deviation"],
    'N2C': ["Nuclear to Cytoplasm Ratio", "Conditions", "Nuclear/Cytoplasm Ratio"],
    'Intensity_pval': ["p-value distribution of FUS enrichment in the Stress Granules", "Conditions", "p-value"],
    'Intensity': ["Absolute FUS Stress Granule Intensity", "Conditions", "FUS Spot Absolute Mean Intensity (AU)"],
    'nIntensity': ["Normalized FUS Stress Granule Intensity", "Conditions", "FUS Spot Normalized Mean Intensity (AU)"],
    'Area': ["Stress Granule Area", "Conditions", "Area of the Stress Granule (pixel)"],
}

SESSION = []


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    if EXPERIMENT:
        experiment, legend = Web_UI.Load_Experiment(EXPERIMENT)
        menu = Web_UI.Generate_Menu(legend)
        f = open('app/templates/menu.html', 'w')
        f.write(menu)
        f.close()
    else:
        f = open('app/templates/menu.html', 'w')
        f.write('<div class="menu_left"></div>')
        f.close()
    response = make_response(render_template("index.html",
                                             title='Home',
                                             session=SESSION))
    response.headers['Cache-Control'] = 'no-cache, no-store'
    return response


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    global EXPERIMENT
    global CUT
    EXPERIMENT = request.form['Experiment_List']
    CUT = request.form['cut']
    return redirect('/index')


@app.route('/save', methods=['GET', 'POST'])
def save():
    global SESSION
    zipf = zipfile.ZipFile('app/static/Session.zip', 'w')
    for s in SESSION:
        zipf.write('app' + s['plot'])
        if s['stats']:
            zipf.write('app' + s['stats'])
    zipf.close()
    return redirect('/static/Session.zip')


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    global CUT
    global SESSION
    global EXPERIMENT
    EXPERIMENT = None
    CUT = None
    SESSION = []


@app.route('/run', methods=['GET', 'POST'])
def run():
    global FILE_ID
    global CUT
    if request.form['exp_list']:
        filename_exp = request.form['exp_list'].replace(',','-').replace('#','$')
        if len(filename_exp) > 20:
            filename_exp = filename_exp[:20]
        data = Web_UI.Fetch_DB(request.form['exp_list'].split(
            ','), request.form['data_choice'], EXPERIMENT, CUT)
        if request.form['plot_ylim']:
            ylim = float(request.form['plot_ylim'])
        else:
            ylim = None
        if request.form['plot_title']:
            title = request.form['plot_title']
        else:
            title = DEFAULT_PLOT_VALUE[request.form["data_choice"]][0]
        if request.form['plot_xlabel']:
            xlabel = request.form['plot_xlabel']
        else:
            xlabel = DEFAULT_PLOT_VALUE[request.form["data_choice"]][1]
        if request.form['plot_ylabel']:
            ylabel = request.form['plot_ylabel']
        else:
            ylabel = DEFAULT_PLOT_VALUE[request.form["data_choice"]][2]
        print request.form['graphtype'] 
        if request.form['graphtype'] == "BoxPlot":
            Web_UI.Boxplot(
                data,
                filename="app/static/BoxPlot_%s_%s_%s.png" % (
                    EXPERIMENT, filename_exp, FILE_ID),
                ylim=ylim,
                title=title,
                xlabel=xlabel,
                ylabel=ylabel)
        elif request.form['graphtype'] == "BoxPlot_pval":
            pval = Web_UI.Fetch_DB(
                request.form['exp_list'].split(','),
                "Intensity_pval",
                EXPERIMENT)
            Web_UI.Nice_Boxplot(
                data,
                pval,
                filename="app/static/BoxPlot_%s_%s_%s.png" % (
                    EXPERIMENT, filename_exp, FILE_ID),
                ylim=ylim,
                title=title,
                xlabel=xlabel,
                ylabel=ylabel)
        if request.form.has_key('stats'):
            if request.form['stats_title']:
                stats_title = request.form['stats_title']
            else:
                stats_title = title
            Web_UI.Stats(
                data,
                test=request.form['stats_test'],
                filename="app/static/Stats_%s_%s_%s.png" % (EXPERIMENT, filename_exp, FILE_ID),
                title=stats_title,
                pval_max=None)
            SESSION.append({
                'id': FILE_ID,
                'title': "dataset:%s _-_ data:%s ID:%s" % (request.form['exp_list'], request.form['data_choice'], FILE_ID),
                'plot': "/static/BoxPlot_%s_%s_%s.png" % (EXPERIMENT, filename_exp, FILE_ID),
                'stats': "/static/Stats_%s_%s_%s.png" % (EXPERIMENT, filename_exp, FILE_ID)})
        else:
            SESSION.append({
                'id': FILE_ID,
                'title': "dataset:%s _-_ data:%s ID:%s" % (request.form['exp_list'], request.form['data_choice'], FILE_ID),
                'plot': "/static/BoxPlot_%s_%s_%s.png" % (EXPERIMENT, filename_exp, FILE_ID),
                'stats': None})
        FILE_ID += 1
    else:
        flash("Please select a condition !")
    return redirect('/index')
