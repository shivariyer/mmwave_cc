from mmparse import *

import os
import sys
import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from glob import glob


def plot_bgtrace(tracename):
    inpdir = os.path.join('traces', 'channels')
    bw = parse_trace_file(os.path.join(inpdir, tracename))
    
    fig = plt.figure(figsize=(12,6), facecolor='w')
    ax = fig.add_subplot(111)
    
    plt.rc('font', size=16)
    
    bw_scaled = [v/1e6 for v in bw] # convert bits to megabits
    avgbw = round(sum(bw_scaled) * 1.0 / len(bw_scaled), 3)
    maxbw = round(max(bw_scaled), 3)
    print(os.linesep + tracename.upper())
    print('Min BW (Mbps):', round(min(bw_scaled), 3))
    print('50th percentile (Mbps):', round(np.median(bw_scaled), 3))
    print('Max BW (Mbps):', maxbw)
    print('Average BW (Mbps):', avgbw)
    print('70th percentile (Mbps):', round(np.percentile(bw_scaled, 70), 3))
    print('70% of max (Mbps):', 0.7 * maxbw)
    
    saveprefix = os.path.join(inpdir, tracename + '_Mbps')
    np.savetxt(saveprefix + '.txt', bw_scaled, fmt='%.6f')
    
    ax.fill_between(np.arange(len(bw)), 0, bw_scaled, color='#F2D19F')
    plt.ylabel('Available BW (Mbps)')
    plt.xlabel('Time (s)')
    plt.title('Average BW = {:.3f} Mbps, max BW = {:.3f} Mbps'.format(avgbw, maxbw))
    plt.xlim([0,60])
    # plt.grid(True, which='both')
    plt.savefig(saveprefix + '.pdf', dpi=1000, bbox_inches='tight')
    plt.show()
    plt.close()


def plot_tput_delay(filepath, ms_per_bin=500, skip_seconds=0, title=None, disp=True, save=False):

    plt.rc('font', size=20)

    print('Parsing delays ...')
    delays, delaytimes = parse_mm_queue_delays(filepath)
    df_delays_full = pd.Series(data=delays, index=pd.Index(delaytimes, name='delaytimes_ms'), name='delay_ms')
    df_delays_full = df_delays_full.groupby(level=0).mean()

    print('Parsing throughput ...')
    data = parse_mm_throughput(filepath, ms_per_bin)
    df_tput_full = pd.concat([data['ingress'], data['throughput'], data['capacity']], axis=1)

    # skip certain amount of time in the beginning (if desired)
    df_delays = df_delays_full[df_delays_full.index > skip_seconds]
    df_tput = df_tput_full[df_tput_full.index > skip_seconds]

    cap = df_tput['capacity']
    tput = df_tput['throughput']
    cap_avg = df_tput['capacity'].mean()
    tput_avg = df_tput['throughput'].mean()
    util = (df_tput['throughput'] * 100.0 / df_tput['capacity']).mean()
    
    fig = plt.figure(figsize=(16,12), facecolor='w')
    
    ax1 = plt.subplot(2, 1, 1)
    p1 = ax1.fill_between(cap.index, 0, cap.values, color='#F2D19F', label='Capacity')
    p2, = ax1.plot(tput.index, tput.values, 'k--', label='Throughput')
    
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    p3, = ax2.plot(df_delays.index, df_delays.values, 'k-', lw=1, label='Delay')
    
    fig.legend((p1, p2, p3), (p1.get_label(), p2.get_label(), p3.get_label()), loc='lower center', ncol=3, fontsize='small')

    if title is None:
        title = os.path.splitext(os.path.basename(filepath))[0]

    fig.suptitle(title)
    
    #ax1.set_title('Cap: {:.2f} Mbps, Tput: {:.2f} Mbps, Util: {:.2f}%'.format(data['capacity_avg'], data['throughput_avg'], (data['throughput_avg'] / data['capacity_avg']) * 100))
    ax1.set_title('Cap: {:.2f} Mbps, Tput: {:.2f} Mbps, Util: {:.2f}%'.format(cap_avg, tput_avg, util))
    ax1.set_ylabel('Mbps')
    
    ax2.set_title('Delay (min, max, avg) = ({:.2f}, {:.2f}, {:.2f})'.format(df_delays.min(), df_delays.max(), df_delays.mean()))
    ax2.set_ylabel('Delay (ms)')
    
    ax2.set_xlabel('Time (sec)')
    
    ax1.tick_params(bottom=0)
    plt.setp(ax1.xaxis.get_ticklabels(), visible=False)
    
    #plt.xlim(0,60)
    #fig.tight_layout()
    fig.subplots_adjust(hspace=0.15)
    #ax1.title.set_position((0.5, 0.85))
    #ax2.title.set_position((0.5, 0.85))
    
    if save:
        savepath = os.path.splitext(filepath)[0]
        print('Saving to', savepath)
        if skip_seconds is None or skip_seconds == 0:
            fig.savefig(savepath + '.png')
        else:
            fig.savefig(savepath + '_skip{}.png'.format(skip_seconds))
        df_delays_full.to_csv(savepath + '_delays.csv', header=True)
        with open(savepath + '_tput.csv', 'w') as fout:
            fout.write('# duration_ms: {}'.format(data['duration_ms']) + os.linesep)
            fout.write('# ingress_avg: {:.3f}'.format(data['ingress_avg']) + os.linesep)
            fout.write('# throughput_avg: {:.3f}'.format(data['throughput_avg']) + os.linesep)
            fout.write('# capacity_avg: {:.3f}'.format(data['capacity_avg']) + os.linesep)
            fout.write('# utilization: {:.3f}'.format(data['utilization']) + os.linesep)
            df_tput_full.to_csv(fout)
    
    if disp:
        plt.show()
    
    plt.close()
    plt.rcdefaults()

    

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title='Types of plots to make',
                                       help='List of valid plot names',
                                       dest='plot_type')
    parser_a = subparsers.add_parser('bgtrace', aliases=['trace'])
    parser_a.add_argument('names', nargs='+', help='Name of a bg trace in traces/channels/')

    parser_b = subparsers.add_parser('tput_delay', aliases=['tput', 'delay'])
    parser_b.add_argument('mmfilepaths', nargs='+', help='Name of a mm log file (*_downlink.csv or *_uplink.csv) or directory')
    parser_b.add_argument('--title', help='Title for plot')
    parser_b.add_argument('--ms-per-bin', type=int, default=500, help='Milliseconds (ms) per bin')
    parser_b.add_argument('--skip-seconds', type=float, default=0, help='Seconds to skip from the beginning to calculate tput and utilization (default: 0)')
    parser_b.add_argument('--dir', default=False, action='store_true')

    args = parser.parse_args()

    if args.plot_type is None:
        print('At least one plot_type should be specified.')
        parser.print_usage()

    elif args.plot_type == 'bgtrace':
        for name in args.names:
            plot_bgtrace(name)

    elif args.plot_type == 'tput_delay':
        if not args.dir:
            for fpath in args.mmfilepaths:
                plot_tput_delay(fpath, args.ms_per_bin, args.title, save=True)
        else:
            # batch generation of tput-delay plots for all results
            assert len(args.mmfilepaths) == 1
            flist = glob(os.path.join(args.mmfilepaths[0], '*_downlink.csv'))
            flist.sort()
            for jj, fpath in enumerate(flist, 1):
                print('{}/{} {}'.format(jj, len(flist), fpath))
                plot_tput_delay(fpath, args.ms_per_bin, args.skip_seconds, args.title, disp=False, save=True)
