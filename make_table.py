import os, sys
import glob
import argparse
import numpy as np
import pandas as pd

from tqdm import tqdm


def generate_results_table(results_dir, key, savepath=None, append=False):

    flist = glob.glob(os.path.join(results_dir, '*_sender_RTT.csv'))

    table = [] # key, tracename, duration, blksize, qsize, mmdelay, avg cap, avg tput, avg util, delay statistics
    for fpath in tqdm(flist, desc='Parsing all output files in \'{}\''.format(results_dir)):
        fname = os.path.basename(fpath)
        if '_Q' in fname:
            trace, duration, blksize, qsize, mmdelay, _ = fname.split('_', 5)
            qsize = int(float(qsize[1:]))
        else:
            trace, duration, blksize, mmdelay, _ = fname.split('_', 4)
            qsize = None
        duration = int(duration[1:])
        mmdelay = int(mmdelay[5:])
        
        df_rtt = pd.read_csv(fpath, header=None, names=['timestamp', 'rtt'])
        df_rtt.set_index('timestamp', inplace=True)
        df_rtt['seconds'] = df_rtt.index.values.round()
        df_rtt = df_rtt.groupby('seconds').mean()
        df_rtt.loc[:, 'rtt'] = df_rtt.rtt.values * 1000 # convert RTT to milliseconds 
        
        df_tput = pd.read_csv(fpath.replace('sender_RTT', 'uplink_mmtput'), skiprows=5, index_col=[0])

        table.append((key, trace, duration, blksize, qsize, mmdelay, df_tput.capacity.mean(), df_tput.throughput.mean(), (df_tput.throughput*100 / df_tput.capacity).mean(), df_rtt.rtt.min(), df_rtt.rtt.max(), df_rtt.rtt.mean(), df_rtt.rtt.std(), df_rtt.rtt.quantile(0.25), df_rtt.rtt.quantile(0.5), df_rtt.rtt.quantile(0.75)))

    df = pd.DataFrame(table, columns=['key', 'trace', 'duration', 'blksize', 'qsize', 'mmdelay', 'capacity', 'throughput', 'utilization', 'delay_min', 'delay_max', 'delay_avg', 'delay_std', 'delay_25', 'delay_50', 'delay_75'])
    df = df.set_index(['key', 'trace', 'duration', 'blksize', 'qsize', 'mmdelay'])
    df.sort_index(level=[0,1,2,3,4,5], inplace=True)

    if savepath is None:
        savepath = os.path.join('results', 'results_{}.csv'.format(key))
    else:
        if os.path.exists(savepath) and append:
            df_existing = pd.read_csv(savepath, index_col=[0,1,2,3,4,5])
            df = pd.concat([df_existing, df], axis=0)

    df.to_csv(savepath, float_format='%.4f')

    return df


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('results_dir', help='Directory where the sim run outputs are present')
    parser.add_argument('save_key', help='Name for this group of results (usually name of the CCA)')
    parser.add_argument('--savepath', '-o', help='Path to save the results table')
    parser.add_argument('--append', '-a', action='store_true', help='Append to an existing table (ignored if --savepath is not provided)')

    args = parser.parse_args()

    if not os.path.exists('results'):
        os.makedirs('results')

    generate_results_table(args.results_dir, args.save_key, savepath=args.savepath, append=args.append)
