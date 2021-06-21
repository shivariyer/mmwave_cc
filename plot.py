from mmparse import *

import os
import sys
import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from glob import glob


def plot_bgtrace(tracename, inpdir):
    plt.rc('font', size=16)
    
    #inpdir = os.path.join('traces', 'channels')
    bw = parse_trace_file(os.path.join(inpdir, tracename + '.trace1'), pkt_size=1472)
    
    fig = plt.figure(figsize=(8,4), facecolor='w')
    ax = fig.add_subplot(111)
    
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
    print('Standard deviation about mean of BW:', np.std(bw_scaled))
    print('75th - 25th Percentile (variation):', round(np.percentile(bw_scaled, 75), 3) - round(np.percentile(bw_scaled, 25), 3))
    
    saveprefix = os.path.join(inpdir, tracename + '_Mbps')
    np.savetxt(saveprefix + '.txt', bw_scaled, fmt='%.6f')
    
    #ax.fill_between(np.arange(len(bw)), 0, bw_scaled, color='#F2D19F')
    ax.plot(bw_scaled, lw=3, c='r')
    ax.set_ylabel('Available BW (Mbps)')
    ax.set_xlabel('Time (s)')
    ax.set_title('Avg BW = {:.3f} Mbps, max BW = {:.3f} Mbps'.format(avgbw, maxbw))
    ax.set_xlim([0,60])
    # ax.grid(True, which='both')
    fig.suptitle(tracename)
    fig.subplots_adjust(bottom=0.2, top=0.8, right=0.98)
    #fig.savefig(saveprefix + '.pdf', dpi=1000, bbox_inches='tight')
    fig.savefig(saveprefix + '.pdf')
    #fig.savefig(saveprefix + '.png', dpi=1000, bbox_inches='tight')
    fig.savefig(saveprefix + '.png')
    plt.show()
    plt.close(fig)


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



def plot_tput_delay_tcpdump(mmlogfilepath, skip_seconds=0, title=None, disp=True, save=False):

    plt.rc('font', size=20)

    rtt_savepath = mmlogfilepath.replace('uplink', 'sender_RTT')
    receiver_tput_savepath = mmlogfilepath.replace('uplink', 'receiver_tput')

    print('Reading tput and RTT ...')
    #df_rtt = pd.read_csv(rtt_savepath, index_col=0, header=None, names=['timestamp', 'rtt'])
    df_rtt = pd.read_csv(rtt_savepath, header=None, names=['timestamp', 'rtt'])
    df_rtt.set_index('timestamp', inplace=True)
    df_rtt['seconds'] = df_rtt.index.values.round()
    df_rtt = df_rtt.groupby('seconds').mean()
    df_rtt.loc[:, 'rtt'] = df_rtt.rtt.values * 1000 # convert RTT to milliseconds 

    #df_tput = pd.read_csv(receiver_tput_savepath, index_col=0, header=None, names=['timestamp', 'tput'])
    df_tput = pd.read_csv(receiver_tput_savepath, header=None, names=['timestamp', 'tput'])
    df_tput.set_index('timestamp', inplace=True)
    df_tput['seconds'] = df_tput.index.values.round()
    df_tput = df_tput.groupby('seconds').sum()
    df_tput.loc[:, 'tput'] = df_tput.tput.values * 8 / 1e6 # convert bytes to megabits

    print('Parsing mm log ...')
    #data = parse_mm_throughput(mmlogfilepath, 1000)
    #df_mm = pd.concat([data['ingress'], data['throughput'], data['capacity']], axis=1)
    df_mm, (q_type, qsize_unit, qsize) = parse_mm_log_simple(mmlogfilepath)
    df_mm['seconds'] = df_mm.index.values.round()
    df_mm = df_mm.drop('queue_bytes', axis=1).groupby('seconds').sum()

    # skip certain amount of time in the beginning (if desired)
    df_rtt = df_rtt[df_rtt.index >= (df_rtt.index[0] + skip_seconds)]
    df_tput = df_tput[df_tput.index >= (df_tput.index[0] + skip_seconds)]
    df_mm = df_mm[df_mm.index >= (df_mm.index[0] + skip_seconds)]

    # cap_mm = df_mm['capacity']
    # tput_mm = df_mm['throughput']
    # util_mm = (df_mm['throughput'] * 100.0 / df_mm['capacity']).mean()
    cap_mm = (df_mm.capacity_bytes * 8 / 1e6)
    tput_mm = (df_mm.egress_bytes * 8 / 1e6)
    dropped_mm = (df_mm.dropped_bytes * 8 / 1e6)
    util_mm = (df_mm.egress_bytes * 100.0 / df_mm.capacity_bytes).mean()
    
    fig = plt.figure(figsize=(16,12), facecolor='w')
    
    ax1 = plt.subplot(3, 1, 1)
    #p1 = ax1.fill_between(cap_mm.index, 0, cap_mm.values, color='#F2D19F', label='Capacity')
    p1 = ax1.fill_between(cap_mm.index - cap_mm.index[0] + 1, 0, cap_mm.values, color='#F2D19F', label='Capacity')
    #p2, = ax1.plot(tput_mm.index, tput_mm.values, 'k--', label='Throughput')
    p2, = ax1.plot(tput_mm.index - tput_mm.index[0] + 1, tput_mm.values, 'k--', label='Throughput')
    #p4, = ax1.plot(df_tput.index - data['init_timestamp'], df_tput.tput, 'r:', label='Throughput (tcpdump)')
    p4, = ax1.plot(df_tput.index - df_tput.index[0] + 1, df_tput.tput, 'r:', label='Throughput (tcpdump)')
    
    ax2 = plt.subplot(3, 1, 2, sharex=ax1)
    p3, = ax2.plot(df_rtt.index - df_rtt.index[0] + 1, df_rtt.rtt, 'k-', lw=1, label='RTT')

    ax3 = plt.subplot(3, 1, 3, sharex=ax1)
    p5, = ax3.plot(dropped_mm.index - dropped_mm.index[0] + 1, dropped_mm.values, 'r-', label='Dropped')
    
    fig.legend((p1, p2, p4, p3, p5), (p1.get_label(), p2.get_label(), p4.get_label(), p3.get_label(), p5.get_label()), loc='lower center', ncol=5, fontsize='small')

    if title is None:
        title = os.path.splitext(os.path.basename(mmlogfilepath))[0]

    fig.suptitle(title)
    
    #ax1.set_title('Cap: {:.2f} Mbps, Tput: {:.2f} Mbps, Util: {:.2f}%'.format(data['capacity_avg'], data['throughput_avg'], (data['throughput_avg'] / data['capacity_avg']) * 100))
    ax1.set_title('Cap: {:.2f} Mbps, Tput: {:.2f} Mbps, Tput (tcpdump): {:.2f} Mbps, Dropped: {:.2f} Mbps, Util: {:.2f}%'.format(cap_mm.mean(), tput_mm.mean(), df_tput.tput.mean(), dropped_mm.mean(), util_mm), fontsize='small')
    ax1.set_ylabel('Mbps')
    
    ax2.set_title('RTT (min, max, avg) = ({:.2f}, {:.2f}, {:.2f})'.format(df_rtt.rtt.min(), df_rtt.rtt.max(), df_rtt.rtt.mean()), fontsize='small')
    ax2.set_ylabel('RTT (ms)')
    
    ax3.set_ylabel('Dropped (Mbps)')

    ax3.set_xlabel('Time (s)')
    
    ax1.tick_params(bottom=0)
    plt.setp(ax1.xaxis.get_ticklabels(), visible=False)
    
    #plt.xlim(0,60)
    #fig.tight_layout()
    fig.subplots_adjust(hspace=0.15)
    #ax1.title.set_position((0.5, 0.85))
    #ax2.title.set_position((0.5, 0.85))
    
    savepath = os.path.splitext(mmlogfilepath)[0]
    if save:
        print('Saving to', savepath)
        if skip_seconds is None or skip_seconds == 0:
            fig.savefig(savepath + '.png')
        else:
            fig.savefig(savepath + '_skip{}.png'.format(skip_seconds))
        #df_delays_full.to_csv(savepath + '_mmdelays.csv', header=True)
    with open(savepath + '_mmtput.csv', 'w') as fout:
        # fout.write('# duration_ms: {}'.format(data['duration_ms']) + os.linesep)
        # fout.write('# ingress_avg: {:.3f}'.format(data['ingress_avg']) + os.linesep)
        # fout.write('# throughput_avg: {:.3f}'.format(data['throughput_avg']) + os.linesep)
        # fout.write('# capacity_avg: {:.3f}'.format(data['capacity_avg']) + os.linesep)
        # fout.write('# utilization: {:.3f}'.format(data['utilization']) + os.linesep)
        df_mm.to_csv(fout)
    
    if disp:
        plt.show()
    
    plt.close('all')
    plt.rcdefaults()

    

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title='Types of plots to make',
                                       help='List of valid plot names',
                                       dest='plot_type')
    parser_a = subparsers.add_parser('bgtrace', aliases=['trace'])
    parser_a.add_argument('names', nargs='+', help='Name of a bg trace in traces/channels/')
    parser_a.add_argument('--dir', default=os.path.join('traces', 'channels'), help='Directory where to find the traces')

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
            plot_bgtrace(name, args.dir)

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
