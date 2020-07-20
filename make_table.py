#!/usr/bin/env python
# coding: utf-8

# In[3]:


import os, sys
import glob
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from tqdm import tqdm
from mmparse import parse_mm_throughput, parse_mm_queue_delays


BDP_dict = {'fanrunning' : 25000,
            'humanmotion' : 60000,
            'stationary' : 300000,
            'walkandturn' : 300000} # approximations of BDPs


def generate_results_table(results_filepath, config, inpdir, mmlog='downlink'):
    #algo_list = ['ccp_aimd', 'ccp_cubic', 'ccp_reno', 'ccp_bbr', 'ccp_copa', 'ccp_bicdctcp', 'ccp_bicdctcpagg']
    #algo_list = ['ccp_cubic', 'ccp_reno', 'ccp_bbr', 'ccp_copa', 'ccp_bicdctcp']
    algo_list = os.listdir(inpdir)
    table = [] # algo + flowcount, tracename, avg cap, avg tput, avg util, delay statistics
    for count, algo in enumerate(algo_list):
        print('{}/{} {}'.format(count, len(algo_list), algo))
        subfolder = algo
        # if algo == 'ccp_cubic' or algo == 'ccp_reno':
        #     subfolder = algo + '_ack'
        # elif algo == 'ccp_bicdctcp' or algo == 'ccp_bicdctcpagg':
        #     subfolder = algo + '_' + cwnd_max
        print(os.path.join(inpdir, '{}', '*_{}_*_{}.csv').format(subfolder, config, mmlog))
        flist = glob.glob(os.path.join(inpdir, '{}', '*_{}_*_{}.csv').format(subfolder, config, mmlog))
        flist.sort()
        for fpath in tqdm(flist):
            fname = os.path.basename(fpath)
            tracename, _, _, buflen, _ = fname.split('_')
            bufsize = '{:.1f}BDP'.format(int(buflen[1:]) / BDP_dict[tracename])
            data = parse_mm_throughput(fpath, verbose=False)
            delays, delaytimes = parse_mm_queue_delays(fpath)
            delays = np.asarray(delays)
            table.append((algo, tracename, bufsize, data['capacity_avg'], data['throughput_avg'], data['utilization'], delays.min(), delays.max(), delays.mean(), delays.std(), np.quantile(delays, 0.25), np.quantile(delays, 0.5), np.quantile(delays, 0.75)))
    print('Table length:', len(table))
    df = pd.DataFrame(table, columns=['algo', 'trace', 'bufsize', 'capacity', 'throughput', 'utilization', 'delay_min', 'delay_max', 'delay_avg', 'delay_std', 'delay_25', 'delay_50', 'delay_75'])
    df = df.set_index(['algo', 'trace', 'bufsize'])
    df.sort_index(level=[0,1,2], inplace=True)
    df.to_csv(results_filepath)

    return df


def plot_result_bars(results_filepath, config, inpdir, algo_list=None, savepath=None, save=True, disp=True):

    if not os.path.exists(results_filepath):
        generate_results_table(results_filepath, config, inpdir)

    df = pd.read_csv(results_filepath, index_col=[0,1,2])

    # select only the algos in algo_list
    df = df.loc[algo_list]
    
    grouped_bufsize = df.groupby(level=2)

    for bufsize, group_bufsize in grouped_bufsize:

        plt.rc('font', size=30)

        # calculations for bar plots
        #n_algos = group_bufsize.index.levels[0].size
        n_algos = len(algo_list)
        n_traces = group_bufsize.index.levels[1].size
        barw = 0.2
        stackgap = (n_algos + 2) * barw
        x_base = np.arange(0, n_traces * stackgap, stackgap)
        xtick_0 = barw * (n_algos-1) / 2
        xtick_end = xtick_0 + n_traces*stackgap

        grouped = group_bufsize.groupby(level=0)
        
        # show util in first plot
        fig1 = plt.figure(figsize=(12,8))
        fig1.suptitle('Comparison across algorithms', fontsize='small')
        ax1 = fig1.add_subplot(111)
        ax1.set_title('Utilization', fontsize='small')
        count = 0
        for name, group in grouped:
            if 'bicdctcp' in name:
                name = name.rsplit('_', 1)[0]
            ax1.bar(x_base + count, group.utilization.values, width=barw, label=name)
            count += barw
        ax1.set_xticks(np.arange(xtick_0, xtick_end, stackgap))
        ax1.set_xticklabels(group_bufsize.index.levels[1].values, rotation=0, fontsize='small')
        ax1.set_ylabel('Throughtput/Capacity (%)')
        ax1.legend(loc=0, ncol=2, fontsize='xx-small', columnspacing=1, framealpha=0.5)

        # show delays in second plot
        fig2 = plt.figure(figsize=(12,8))
        fig2.suptitle('Comparison across algorithms', fontsize='small')
        ax2 = fig2.add_subplot(111)
        ax2.set_title('Per-packet delays', fontsize='small')
        count = 0
        for name, group in grouped:
            if 'bicdctcp' in name:
                name = name.rsplit('_', 1)[0]
            ax2.bar(x_base + count, group.delay_avg.values, width=barw, label=name)
            errorbars = np.abs(group.delay_50.values - group[['delay_25','delay_75']].values.T)
            ax2.errorbar(x_base + count, group.delay_50.values, yerr=errorbars, capsize=3, capthick=2, fmt='ko', barsabove=True, ecolor='k')
            count += barw
        ax2.set_xticks(np.arange(xtick_0, xtick_end, stackgap))
        ax2.set_xticklabels(group_bufsize.index.levels[1].values, rotation=0, fontsize='small')
        ax2.set_ylabel('Delay (ms)')
        ax2.legend(loc=0, ncol=2, fontsize='xx-small', columnspacing=1, framealpha=0.5)

        if save:
            fig1.savefig(savepath + '_{}_Util.png'.format(bufsize))
            fig1.savefig(savepath + '_{}_Util.pdf'.format(bufsize))
            fig2.savefig(savepath + '_{}_Delay.png'.format(bufsize))
            fig2.savefig(savepath + '_{}_Delay.pdf'.format(bufsize))

    if disp:
        plt.show()

    plt.close('all')

    return


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir', help='Directory where the sim run outputs are present')
    parser.add_argument('--config', default='T60_128KiB', help='Sim run parameters')
    parser.add_argument('--cwnd_max', required=True, help='For selecting the BIC+DCTCP output')

    args = parser.parse_args()

    results_filepath = 'results/NEW/results_{}.csv'.format(args.config)

    #cwnd_max = 800000

    algo_list = ['ccp_reno_ack', 'ccp_cubic_ack', 'ccp_bbr', 'ccp_copa', 'ccp_bicdctcp_{}'.format(args.cwnd_max)]

    savepath_prefix = 'results/NEW/results_{}_cwnd{}'.format(args.config, args.cwnd_max)
    plot_result_bars(results_filepath, args.config, args.output_dir, algo_list, savepath_prefix, save=True, disp=False)
