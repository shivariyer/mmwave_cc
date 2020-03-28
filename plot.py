from mmparse import *

import os
import sys 
import matplotlib.pyplot as plt
import numpy as np

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
    print('Average BW (Mbps):', avgbw)
    print('Max BW (Mbps):', maxbw)
    print('70th percentile (Mbps):', round(np.percentile(bw_scaled, 70), 3))
    print('70% of max (Mbps):', 0.7 * maxbw)
    
    np.savetxt(saveprefix + '.txt', bw_scaled, fmt='%.6f')
    
    ax.fill_between(np.arange(len(BW)), 0, bw_scaled, color='#F2D19F')
    plt.ylabel('Available BW (Mbps)')
    plt.xlabel('Time (s)')
    plt.title('Average BW = {:.3f} Mbps, max BW = {:.3f} Mbps'.format(avgbw, maxbw))
    plt.xlim([0,60])
    # plt.grid(True, which='both')
    saveprefix = os.path.join(inpdir, tracename + '_Mbps')
    plt.savefig(saveprefix + '.pdf',dpi=1000,bbox_inches='tight')
    plt.show()
    plt.close()


def plot_tput_delay(filepath, ms_per_bin=500, title=None, disp=True, save=False):

    plt.rc('font', size=20)
    
    delays, delaytimes = parse_mm_queue_delays(filepath)
    data = parse_mm_throughput(filepath, ms_per_bin)
    
    cap = data['capacity']
    tput = data['throughput']
    
    fig = plt.figure(figsize=(12,12), facecolor='w')
    
    ax1 = plt.subplot(2, 1, 1)
    p1 = ax1.fill_between(cap.index, 0, cap.values, color='#F2D19F', label='Capacity')
    p2, = ax1.plot(tput.index, tput.values, 'k--', label='Throughput')
    
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    p3, = ax2.plot(delaytimes, delays, 'k-', lw=1, label='Delay')
    
    fig.legend((p1, p2, p3), (p1.get_label(), p2.get_label(), p3.get_label()), loc='lower center', ncol=3, fontsize='small')
    
    if title is not None:
        fig.suptitle(title)
    
    ax1.set_title('Cap: {:.2f} Mbps, Tput: {:.2f} Mbps, Util: {:.2f}%'.format(data['capacity_avg'], data['throughput_avg'], (data['throughput_avg'] / data['capacity_avg']) * 100))
    ax1.set_ylabel('Mbps')
    
    ax2.set_title('Delay (min, max, avg) = ({:.2f}, {:.2f}, {:.2f})'.format(min(delays), max(delays), sum(delays)/len(delays)))
    ax2.set_ylabel('Delay (ms)')
    
    ax2.set_xlabel('Time (sec)')
    
    ax1.tick_params(bottom=0)
    plt.setp(ax1.xaxis.get_ticklabels(), visible=False)
    
    #plt.xlim(0,60)
    #fig.tight_layout()
    #fig.subplots_adjust(bottom=0.2, hspace=0)
    #ax1.title.set_position((0.5, 0.85))
    #ax2.title.set_position((0.5, 0.85))
    
    if save:
        savepath = os.path.splitext(filepath)[0] + '.png'
        print('Saving to', savepath)
        fig.savefig(savepath)
    
    if disp:
        plt.show()
    
    plt.close()
    plt.rcdefaults()


if __name__ == '__main__':

    # if len(sys.argv) < 2:
    #     print('Usage: {} <mm_log_file>'.format(sys.argv[0]))
    #     sys.exit(-1)
    
    # plot_tput_delay(sys.argv[1], title='Title')
    
    # batch generation of tput-delay plots for all results
    for ii, algo in enumerate(['bbr', 'bicdctcp_100000', 'bicdctcp_1000000', 'copa', 'cubic', 'reno'], 1):
        print(os.linesep, ii, algo, os.linesep)
        flist = glob('output/{}/*/*_downlink.csv'.format(algo))
        flist.sort()
        for jj, fpath in enumerate(flist, 1):
            print('{}/{} {}'.format(jj, len(flist), fpath))
            plot_tput_delay(fpath, title=algo.upper(), disp=False, save=True)
