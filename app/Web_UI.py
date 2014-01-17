#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
# from pylab import *
from copy import *
import sqlite3 as lite
CUT = True


def Cut(l):
    l_sort = sorted(l)
    lengh = len(l_sort)
    if CUT:
        l_cut = l_sort[int(0.025 * lengh):int(0.975 * lengh)]
    else:
        l_cut = l_sort
    return l_cut


def Fetch_DB(Times_Conditions, data, db_name, cut=None):
    tables = {
        'Counts': '_Cells',
        'Nuclear_Mean_Int': '_Cells',
        'Nuclear_Mean_Std': '_Cells',
        'Cytoplasm_Mean_Int': '_Cells',
        'Cytoplasm_Mean_Std': '_Cells',
        'N2C': '_Cells',
        'Intensity_pval': '_Cells',
        'Intensity': '_Spots',
        'nIntensity': '_Spots',
        'Area': '_Spots',
    }
    Times_Conditions = [(i.split('_')[0], i.split('_')[1])
                        for i in Times_Conditions]
    con = lite.connect('%s.db' % db_name)
    with con:
        cur = con.cursor()
        res = {'legend': [], 'data': []}
        for Time, Condition in Times_Conditions:
            table = db_name + tables[data]
            cur.execute(
                "SELECT %s FROM %s WHERE Time='%s' AND Condition='%s' ;" %
                (data, table, Time, Condition))
            rows = cur.fetchall()
            if cut:
                res['data'].append(np.array(Cut([r[0] for r in rows])))
            else:
                res['data'].append(np.array([r[0] for r in rows]))
            cur.execute("SELECT Name FROM %s_Legend WHERE ShortName='%s';" %
                        (db_name, Time))
            time = cur.fetchone()[0]
            cur.execute("SELECT Name FROM %s_Legend WHERE ShortName='%s';" %
                        (db_name, Condition))
            cond = cur.fetchone()[0]
            res['legend'].append("%s\n%s" % (time, cond))
        return res


def Load_Experiment(db_name):
    con = lite.connect('app/db/%s.db' % db_name)
    with con:
        cur = con.cursor()
        cur.execute("SELECT Type,ShortName,Name FROM %s_Legend;" % db_name)
        rows = cur.fetchall()
        nb_time = np.sum([1 if r[0] == 0 else 0 for r in rows])
        nb_cond = np.sum([1 if r[0] == 1 else 0 for r in rows])
        print nb_time, nb_cond
        time, cond = [], []
        ltime, lcond = [], []
        for r in rows:
            if r[0] == 0:
                time.append(r[1])
                ltime.append("%s:%s" % (r[1], r[2]))
            else:
                cond.append(r[1])
                lcond.append("%s:%s" % (r[1], r[2]))
        experiment = np.zeros((nb_time, nb_cond), dtype='|S30')
        legend = np.zeros((nb_time + 1, nb_cond + 1), dtype='|S30')
        for i in range(len(time)):
            for j in range(len(cond)):
                experiment[i][j] = "%s_%s" % (time[i], cond[j])
                legend[i + 1][j + 1] = "%s_%s" % (time[i], cond[j])
        for i in range(len(ltime)):
            legend[i + 1][0] = ltime[i]
        for j in range(len(lcond)):
            legend[0][j + 1] = lcond[j]
        return (experiment, legend)


def Generate_Menu(legend):
    template = '''<div class="menu_left">\n'''
    for row in range(len(legend)):
        template += '\t<div class="menu_row">\n'
        if row == 0:
            for el in legend[row]:
                template += __Menu_Legend__(el)
        else:
            template += __Menu_Legend__(legend[row][0])
            for el in legend[row][1:]:
                template += __Menu_Input__(el)
        template += '\t</div>'
    template += "</div>\n"
    return template


def __Menu_Input__(name):
    return '\t\t<div class="menu_check menu_cell"><input type="checkbox" id="%s" name="checkbox" onchange="checked_cliked()"></div>\n' % name


def __Menu_Legend__(name):
    if name:
        return '\t\t<div class="menu_cell menu_legend" id="%s" onclick="select_all(' % name.split(':')[0] + "'%s'" % name.split(':')[0]  +')" active="0">%s</div>\n' % name.split(':')[1]
    else:
        return '\t\t<div class="menu_cell menu_legend" id="SELECTALL" onclick="select_all(' + "'_'" + ')" active="0">ALL</div>\n'


def under5(x):
    x = np.array(sorted(x))
    x1 = (x > 0.02).astype(np.int)
    r = x1.sum() / float(len(x))
    return r


def Stats(res, test='Mann', filename=None, title="title", pval_max=None):
        Legend = res['legend']
        data = res['data']
        nb_data = len(data)
        if not pval_max:
            pval_max = round(0.05 / nb_data, 3)
        p = np.ones((nb_data, nb_data))
        p.fill(2)
        for i in range(nb_data):
            for j in range(i, nb_data):
                if i != j:
                    if test == "Mann":
                        u, pval = stats.mannwhitneyu(data[i], data[j])
                        pval = pval * 2
                    elif test == "ttest":
                        u, pval = stats.ttest_ind(
                            data[i], data[j], equal_var=False)
                    if pval > pval_max:
                        p[i][j] = 1
                    else:
                        p[i][j] = 0
        fig = plt.figure(figsize=(8, 8))
        plt.subplots_adjust(left=0.2, right=0.9, top=0.8, bottom=0.2)
        if test == 'Mann':
            print "Mann Witney U Test\n White p-value > %s = Similar \n Red p-value < %s = Different" % (pval_max, pval_max)
            fig.suptitle(
                "Mann Witney U Test\n White p-value > %s = Similar \n Red p-value < %s = Different" % (pval_max, pval_max))
        elif test == 'ttest':
            fig.suptitle(
                "Welch ttest\n White p-value > %s = Similar \n Red p-value < %s = Different" % (pval_max, pval_max))
        s = fig.add_subplot(111)
        s.set_title(title)
        s.imshow(p, cmap=get_cmap('RdGy'), interpolation='none')
        s.axes.set_xticklabels([""] + Legend, rotation=70, fontsize=9)
        s.axes.set_yticklabels([""] + Legend, rotation=0, fontsize=9)
        if filename:
            fig.savefig(filename)
        else:
            fig.show()


def Nice_Boxplot(res, pval, filename, ylim=None, title="Title", xlabel="xlabel", ylabel="ylabel", n=5):
        legend = res['legend']
        data = res['data']
        pval = pval['data']
        nbbox = len(data)
        fig = plt.figure(figsize=(10, 6))
        s = fig.add_subplot(111)
        ax1 = s.axes
        plt.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.19)
        b = s.boxplot(data)
        plt.setp(b['boxes'], color='black')
        plt.setp(b['whiskers'], color='black')
        plt.setp(b['fliers'], color='red', marker='+')
        # s.set_ylim(top=1500)
        s.axes.set_xticklabels(legend, rotation=20, fontsize=8)
        ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                       alpha=0.9)
        ax1.set_axisbelow(True)
        if ylim:
            s.set_ylim(top=ylim)
        s.set_title(title)
        s.set_xlabel(xlabel)
        s.set_ylabel(ylabel)
        medians = range(nbbox)
        pval_lab = []
        for i in range(nbbox):
            box = b['boxes'][i]
            boxX = []
            boxY = []
            pv = under5(pval[i])
            pval_lab.append(pv)
            for j in range(n):
                boxX.append(box.get_xdata()[j])
                boxY.append(box.get_ydata()[j])
            y_red_top = boxY[1] + ((boxY[2] - boxY[1]) * pv)
            boxY_green = copy(boxY)
            boxY_green[0] = y_red_top
            boxY_green[1] = y_red_top
            boxY_green[4] = y_red_top
            boxY_red = copy(boxY)
            boxY_red[2] = y_red_top
            boxY_red[3] = y_red_top
            boxCoords_red = zip(boxX, boxY_red)
            boxCoords_green = zip(boxX, boxY_green)
            # print pv
            boxPolygon = Polygon(boxCoords_green, facecolor='lightgreen')
            ax1.add_patch(boxPolygon)
            boxPolygon = Polygon(boxCoords_red, facecolor='darkred')
            ax1.add_patch(boxPolygon)
            med = b['medians'][i]
            medianX = []
            medianY = []
            for j in range(2):
                medianX.append(med.get_xdata()[j])
                medianY.append(med.get_ydata()[j])
                plt.plot(medianX, medianY, 'k')
                medians[i] = medianY[0]
            plt.plot([np.average(med.get_xdata())], [np.average(data[i])],
                     color='w', marker='*', markeredgecolor='k')
        pos = np.arange(nbbox) + 1
        upperLabels = [str(np.round(bla, 2)) for bla in medians]
        pval_lab = [
            str(np.round((1 - bla) * 100, 1)) + '%' for bla in pval_lab]
        bottom, top = s.axes.get_ylim()
        for tick, label in zip(range(nbbox), ax1.get_xticklabels()):
            ax1.text(pos[tick], top - (top * 0.05), pval_lab[tick],
                     horizontalalignment='center', size='x-small', weight='bold',
                     color='black')
            ax1.text(
                pos[tick], bottom + (abs(bottom * 0.1)), upperLabels[tick],
                horizontalalignment='center', size='x-small', weight='bold',
                color='black')
        plt.figtext(
            0.60, 0.08, 'pval < 0.05 FUS background VS spots per cells',
            backgroundcolor='lightgreen', color='black', weight='roman',
            size='x-small')
        plt.figtext(
            0.60, 0.045, 'pval > 0.05 FUS background VS spots per cells',
            backgroundcolor='darkred',
            color='black', weight='roman', size='x-small')
        plt.figtext(0.60, 0.013, '*', color='white', backgroundcolor='silver',
                    weight='roman', size='medium')
        plt.figtext(
            0.615, 0.013, ' Average Value', color='black', weight='roman',
            size='x-small')
        print "DONE"
        if filename:
            print "SAVED"
            fig.savefig(filename)
        else:
            fig.show()


def Boxplot(res, filename=None, ylim=None, title="Title", xlabel="xlabel", ylabel="ylabel", n=5):
        legend = res['legend']
        data = res['data']
        nbbox = len(data)
        fig = plt.figure(figsize=(10, 6))
        s = fig.add_subplot(111)
        ax1 = s.axes
        plt.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.15)
        b = s.boxplot(data)
        plt.setp(b['boxes'], color='black')
        plt.setp(b['whiskers'], color='black')
        plt.setp(b['fliers'], color='red', marker='+')
        if ylim:
            s.set_ylim(top=ylim)
        s.axes.set_xticklabels(legend, rotation=20, fontsize=8)
        ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                       alpha=0.9)
        ax1.set_axisbelow(True)
        s.set_title(title)
        s.set_xlabel(xlabel)
        s.set_ylabel(ylabel)
        medians = range(nbbox)
        mean = range(nbbox)
        for i in range(len(b['boxes'])):
            box = b['boxes'][i]
            boxX = []
            boxY = []
            for j in range(n):
                boxX.append(box.get_xdata()[j])
                boxY.append(box.get_ydata()[j])
            boxCoords = zip(boxX, boxY)
            boxPolygon = Polygon(boxCoords, facecolor='orange')
            ax1.add_patch(boxPolygon)
            med = b['medians'][i]
            medianX = []
            medianY = []
            for j in range(2):
                medianX.append(med.get_xdata()[j])
                medianY.append(med.get_ydata()[j])
                plt.plot(medianX, medianY, 'k')
                medians[i] = medianY[0]
                mean[i] = np.mean(data[i])
            plt.plot([np.average(med.get_xdata())], [np.average(data[i])],
                     color='w', marker='*', markeredgecolor='k')
        pos = np.arange(nbbox) + 1
        upperLabels = [str(np.round(bla, 2)) for bla in mean]
        bottom, top = s.axes.get_ylim()
        for tick, label in zip(range(nbbox), ax1.get_xticklabels()):
            ax1.text(
                pos[tick], top - (top * 0.05), upperLabels[tick],
                horizontalalignment='center', size='x-small', weight='bold',
                color='black')
        plt.figtext(0.80, 0.013, '*', color='white', backgroundcolor='silver',
                    weight='roman', size='medium')
        plt.figtext(
            0.815, 0.013, ' Average Value', color='black', weight='roman',
            size='x-small')
        if filename:
            fig.savefig(filename)
        else:
            fig.show()
