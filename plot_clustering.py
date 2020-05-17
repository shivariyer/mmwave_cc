import random
import os
import re
import glob
import itertools
import numpy as np
import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.pyplot as plt

from sklearn import metrics
from matplotlib.ticker import MultipleLocator

plt.rc('ps', useafm=True)
plt.rc('pdf', use14corefonts=True)


def plot_cluster_scatter_nf1 (data, colors_true, colors_pred, names):
    
    plt.rc('font', size=18)
    
    cm = plt.cm.get_cmap('RdYlBu')
    nfeatures = len(names)
    
    assert nfeatures == 1
    
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True, figsize=(8,4))
    
    data = data[:]
    colors_true = colors_true[:]
    colors_pred = colors_pred[:]

    f1_0 = round(100 * metrics.f1_score(colors_true, colors_pred, pos_label=0, average='binary'), 3)
    f1_1 = round(100 * metrics.f1_score(colors_true, colors_pred, pos_label=1, average='binary'), 3)
    f1_macro = round(100 * metrics.f1_score(colors_true, colors_pred, average='macro'), 3)
    
    print('F1 (1):', f1_1, 'F1 (0):', f1_0, 'F1 (macro):', f1_macro)
    
    # rtt on x-axis 
    rtt_yes_true = data[colors_true == 1]
    rtt_no_true = data[colors_true == 0]
    obj1 = ax1.scatter(rtt_no_true, np.zeros(len(rtt_no_true)), c='w', alpha = 0.3, s=100, edgecolors='b', label='No cong')
    obj2 = ax1.scatter(rtt_yes_true, np.zeros(len(rtt_yes_true)), c='r', alpha = 1.0, s=36, label='Cong')
    # ax1.scatter(rtt_no_true, iat_no_true, c='b', alpha = 0.3, s=36, marker='x')
    ax1.set_title('True clusters', fontsize='small')
    ax1.set_xlabel(r'RTT$(t-1)$')
    # ax1.set_ylabel(r'IAT$(t-1)$')
    ax1.tick_params(direction='out', left=0, right=0, labelleft=0, length=5, pad=5)
    #ax1.legend([obj1], [obj1.get_label()], loc=0, fontsize='small')
    
    # rtt on x-axis and iat on y-axis
    rtt_yes_pred = data[colors_pred == 1]
    rtt_no_pred = data[colors_pred == 0]
    ax2.scatter(rtt_no_pred, np.zeros(len(rtt_no_pred)), c='w', alpha = 0.3, s=100, edgecolors='b')
    ax2.scatter(rtt_yes_pred, np.zeros(len(rtt_yes_pred)), c='r', alpha = 1.0, s=36)
    # ax2.scatter(rtt_no_true, iat_no_true, c='b', alpha = 0.3, s=36, marker='x')
    ax2.set_title('Predicted clusters', fontsize='small')
    ax2.set_xlabel(r'RTT$(t-1)$')
    # ax2.set_ylabel(r'IAT$(t-1)$')
    # ax2.yaxis.get_label().set_visible(False)
    ax2.tick_params(direction='out', left=0, right=0, labelleft=0, length=5, pad=5)
    #ax2.legend([obj2], [obj2.get_label()], loc=0, fontsize='small')
    
    # fig.legend((obj1, obj2), (obj1.get_label(), obj2.get_label()), loc='upper center', ncol=2, fontsize='small')
    fig.suptitle('Macro average F1 score: {}'.format(f1_macro), fontsize='small')
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.2, top=0.82, wspace=0.02)
    
    #plt.show()
    
    return fig


def plot_cluster_scatter_nf2 (data, colors_true, colors_pred, names):
    
    plt.rc('font', size=18)
    
    cm = plt.cm.get_cmap('RdYlBu')
    nfeatures = len(names)
    
    assert nfeatures == 2
    
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True, figsize=(8,4))
    
    data = data[:,:]
    colors_true = colors_true[:]
    colors_pred = colors_pred[:]

    f1_0 = round(100 * metrics.f1_score(colors_true, colors_pred, pos_label=0, average='binary'), 3)
    f1_1 = round(100 * metrics.f1_score(colors_true, colors_pred, pos_label=1, average='binary'), 3)
    f1_macro = round(100 * metrics.f1_score(colors_true, colors_pred, average='macro'), 3)
    
    #print('Accuracy:', metrics.accuracy_score(colors_true, colors_pred))
    #print('-'*20)
    print('F1 (1):', f1_1, 'F1 (0):', f1_0, 'F1 (macro):', f1_macro)
    #print('-'*20)
    
    # rtt on x-axis and iat on y-axis
    rtt_yes_true, iat_yes_true = data[colors_true == 1,:].T
    rtt_no_true, iat_no_true = data[colors_true == 0,:].T
    obj1 = ax1.scatter(rtt_yes_true, iat_yes_true, c='r', alpha = 1.0, s=36, label='Cong')
    obj2 = ax1.scatter(rtt_no_true, iat_no_true, c='w', alpha = 0.3, s=64, edgecolors='b', label='No cong')
    # ax1.scatter(rtt_no_true, iat_no_true, c='b', alpha = 0.3, s=36, marker='x')
    ax1.set_title('True clusters', fontsize='small')
    ax1.set_xlabel(r'RTT$(t-1)$')
    ax1.set_ylabel(r'IAT$(t-1)$')
    ax1.tick_params(direction='out', length=5, pad=5)
    # ax1.legend([obj1], [obj1.get_label()], loc=0, fontsize='small')
    
    # rtt on x-axis and iat on y-axis
    rtt_yes_pred, iat_yes_pred = data[colors_pred == 1,:].T
    rtt_no_pred, iat_no_pred = data[colors_pred == 0,:].T
    ax2.scatter(rtt_yes_pred, iat_yes_pred, c='r', alpha = 1.0, s=36)
    ax2.scatter(rtt_no_pred, iat_no_pred, c='w', alpha = 0.3, s=64, edgecolors='b')
    # ax2.scatter(rtt_no_true, iat_no_true, c='b', alpha = 0.3, s=36, marker='x')
    ax2.set_title('Predicted clusters', fontsize='small')
    ax2.set_xlabel(r'RTT$(t-1)$')
    # ax2.set_ylabel(r'IAT$(t-1)$')
    # ax2.yaxis.get_label().set_visible(False)
    ax2.tick_params(left=0, direction='out', length=5, pad=5)
    # ax2.legend([obj2], [obj2.get_label()], loc=0, fontsize='small')
    
    # fig.legend((obj1, obj2), (obj1.get_label(), obj2.get_label()), loc='upper center', ncol=2, fontsize='small')
    fig.suptitle('Macro average F1 score: {}'.format(f1_macro), fontsize='small')
    fig.subplots_adjust(right=0.98, bottom=0.2, top=0.82, wspace=0.02)
    
    # plt.show()
    
    return fig


def MyScatterMat (data, colors, centroids, names):
    cm = plt.cm.get_cmap('RdYlBu')
    _, cols = data.shape
    
    fig, axes = plt.subplots(nrows=cols, ncols=cols)
    fig.subplots_adjust(hspace=0.0, wspace=0.0)
    
    # Plot the data.
    for i,j in itertools.product(range(0,cols), range(0,cols)):
        spacing = 0.2 # This can be your user specified spacing. 
        minorLocator = MultipleLocator(spacing)
        axes[i,j].yaxis.set_minor_locator(minorLocator)
        axes[i,j].xaxis.set_minor_locator(minorLocator)
        axes[i,j].grid(which = 'minor')   
        for tic in axes[i,j].xaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
            tic.label1On = tic.label2On = False
        for tic in axes[i,j].yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
            tic.label1On = tic.label2On = False      
        if axes[i,j].is_last_col():
            axes[i,j].yaxis.set_label_position('right')
            axes[i,j].set_ylabel(names[i])
            axes[i,j].yaxis.set_visible(True)
        if axes[i,j].is_first_col():
            axes[i,j].set_ylabel(names[i])
            axes[i,j].yaxis.set_visible(True)
        if axes[i,j].is_last_row():
            axes[i,j].set_xlabel(names[j])
            axes[i,j].xaxis.set_visible(True)
        if axes[i,j].is_first_row():
            axes[i,j].xaxis.set_label_position('top')
            axes[i,j].set_xlabel(names[j])
            axes[i,j].xaxis.set_visible(True)  
        if i<=j:
            fig.delaxes(axes[i,j])    
            # elif i == j: 
            #   counts, bins = np.histogram(data[:, i], density=True)
            #   axes[i,j].hist(bins[:-1], bins, weights=counts, alpha=0.4)
        else:  
            non_cm = data[colors == 0]
            cm = data[colors == 1]
            axes[i,j].scatter(non_cm[:,0], non_cm[:,1], c='blue', alpha = 0.02, s=10)
            axes[i,j].scatter(cm[:,0], cm[:,1], c='red', alpha = 0.02, s=5)
            # axes[i,j].scatter(data[:, j], data[:, i], c=colors, alpha = 0.02, s=5, cmap=cm)
            # axes[i,j].scatter(centers[:, j], centers[:, i], c='k', alpha = 1, s=15)  
        axes[i,j].figure.set_size_inches(5, 5)
    return fig  


def giveSuffix(fname):
    traces = ['humanmotion', 'fanrunning', 'stationary', 'walkandturn']
    for trace in traces:
        if trace in fname:
            return trace + str(int(random.random()*1000))
    return "SHOULD_NOT_REACH_THIS" + str(int(random.random()*1000))

def do_plot(inpdir, history):
    ''' All the output files in \'inpdir\' will be collected. '''
    
    # allfeatures = np.asarray(['RTT-4', 'IAT-4', 'RTT-3', 'IAT-3', 'RTT-2', 'IAT-2', 'RTT-1', 'IAT-1'])
    feats = []
    for i in range(history, 0, -1):
        feats.append(f'RTT-{i}')
        feats.append(f'IAT-{i}')
    
    allfeature = np.assarray([feats])
    #pat = re.compile('(fset(\d+)_H\d+_(.+)_sp(\d{2})_tr(.+)_w(\d)_pkt(\d{2})_s(.+))\.')

    allfiles = glob.glob(os.path.join(inpdir, 'report_*_H1_*.txt'))
    allfiles.sort()

    figdir = os.path.join(inpdir, 'figures')
    if not os.path.exists(figdir):
        os.mkdir(figdir)
    
    for fpath in allfiles:

        fname = os.path.basename(fpath)
        # m = pat.search(fname)
        # fsuffix, fset, tracename, bint, sendrate, weight, npkts, s = m.groups()
        # print('fset = {}, tracename = {}, bint = {}, sendrate = {}, weight = {}, npkts = {} sigma = {}'.format(fset, tracename, bint, sendrate, weight, npkts, s))
        fsuffix = giveSuffix(fname)
        fset = '1'

        auxY, y_pred = np.loadtxt(os.path.join(inpdir, 'labels_{}.txt'.format(fsuffix)), skiprows=1, unpack=True)
        centroids = np.loadtxt(os.path.join(inpdir, 'centroids_{}.csv'.format(fsuffix)), delimiter=',', skiprows=1)
        data = np.loadtxt(os.path.join(inpdir, 'finaldata_{}.csv'.format(fsuffix)), delimiter=',', skiprows=1)

        if fset == '1':
            features = allfeatures[[6,7]]
            fig = plot_cluster_scatter_nf2(data, auxY, y_pred, features)
        elif fset == '2':
            features = allfeatures[[6]] # using only sender size info
            fig = plot_cluster_scatter_nf1(data, auxY, y_pred, features)
        else:
            raise Exception('fset needs to be \'1\' or \'2\' only')
        
        fig.savefig(os.path.join(figdir, 'cluster_{}.png'.format(fsuffix)))
        plt.close(fig)
        
        # print(classification report)
        #print(metrics.classification_report(auxY, y_pred, labels=[0,1], target_names=['No congestion','Congestion']))
        
    return


def plot_bars_compare_hyperparams(inpdir, fset, histlen, tracename, sp, sendrate, metric='f1-score', row='macro avg'):

    '''The three hyperparams are 'weight', 'npkts' and 'sigma'. Bars will
    be plotted to show the impact of these three hyperparams.

    Options for metric are: 'precision', 'recall' and 'f1-score'

    Options for row are: 'No congestion', 'congestion', 'micro avg', 'macro avg', 'weighted avg'
    
    '''

    row_shortnames_dict = {'No congestion' : '0',
                           'Congestion' : '1',
                           'micro avg' : 'uavg',
                           'macro avg' : 'mavg',
                           'weighted avg' : 'wavg'}
    
    metric_shortnames_dict = {'precision' : 'prec',
                              'recall' : 'recall',
                              'f1-score' : 'f1'}
    
    figdir = os.path.join('figures', 'bars_compare_hyperparams')
    if not os.path.exists(figdir):
        os.mkdir(figdir)
    
    weight_list = ['1', '3', '5', '7', '9']
    npkts_list = ['01', '10', '50']
    #npkts_list = ['01']
    s_list = ['1', '2', '3', 'INF']
    
    color_list = ['r', 'b', 'g', 'y', 'm', 'c']
    
    prefix = 'report_fset{}_H{}_{}_sp{:02d}_tr{}'.format(fset, histlen, tracename, sp, sendrate)

    nbars = len(npkts_list) * len(s_list)
    barw = 0.6 / nbars

    fig = plt.figure(figsize=(12,12))
    ax = fig.add_subplot(111)
    fig.suptitle('fset={}, H={}, {}, bint={}, {}'.format(fset, histlen, tracename, sp, sendrate))
    
    xmid = np.arange(len(weight_list))
    
    count = -1
    
    for cind, npkts in enumerate(npkts_list):
        
        color = color_list[cind]
        
        for s in s_list:
            
            count += 1
            
            suffix = 'pkt{}_s{}'.format(npkts, s)
            
            # if midpoint of bar group is 'xmid', and there are 'n'
            # bars of equal width 'barw' in the group, with zero
            # spacing, then, regardless of whether 'n' is odd or
            # event, the midpoint of the first bar in the group is
            # given by x1 = xmid - ((n-1)/2)*barw. Subsequent
            # midpoints are xi = {x1 + i*barw, 0 <= i <= n-1}
            
            x = xmid - ((nbars - 1)/2) * barw + count * barw
            y = []
            
            for w in weight_list:
                
                with open(os.path.join(inpdir, prefix + '_w{}_{}.txt'.format(w, suffix))) as fin:
                    for line in fin:
                        if row in line:
                            fields = line.rsplit(None, 4)[1:-1]
                            if metric == 'precision':
                                y.append(float(fields[0]))
                            elif metric == 'recall':
                                y.append(float(fields[1]))
                            else:
                                y.append(float(fields[2]))
                            break

            b = ax.bar(x, y, barw, color=color, edgecolor='k')

        b.set_label('npkts {}'.format(npkts))

    
    ax.legend(ncol=4, loc=0)
    ax.set_xticks(xmid)
    ax.set_xticklabels(weight_list)
    ax.set_xlabel('Weights')
    ax.set_ylim(0,1)
    ax.set_ylabel('{} ({})'.format(metric, row))
    ax.set_title('{} ({}) as function of hyperparameters'.format(metric, row))

    #plt.show()
    
    fig.savefig(os.path.join(figdir, '{}_tr{}_sp{:02d}_H{}_fset{}_{}_{}.png'.format(tracename, sendrate, sp, histlen, fset, metric_shortnames_dict[metric], row_shortnames_dict[row])))

    plt.close(fig)
            
    pass


if __name__ == '__main__':

    datadir = 'results/clustering_202005170023'
    do_plot(datadir, history=20)
    assert False

    # fset = '1'
    # inpdir = 'results/clustering_201909251402' if fset == '1' else 'results/clustering_201909251501'
    # histlen = 1
    # tracename = 'still_on_the_table_with_hands2'

    # sp = 5
    # sendrate = '620-680'
    
    # # plot_bars_compare_hyperparams(inpdir, fset, histlen, tracename, sp, sendrate, 'f1-score', 'macro avg')

    # for fset in ['1', '2']:
    #     inpdir = 'results/clustering_201909251402' if fset == '1' else 'results/clustering_201909251501'
        
    #     for histlen in [1, 2, 3, 4]:

    #         for tracename in ['walkandturn5g', 'still_on_the_table_with_hands2']:

    #             print(fset, histlen, tracename)
                
    #             plot_bars_compare_hyperparams(inpdir, fset, histlen, tracename, sp, sendrate, 'f1-score', 'macro avg')
