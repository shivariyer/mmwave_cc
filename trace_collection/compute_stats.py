import os
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm

# Some delay values are negative possibly due to the fault of
# gettimeofday() in the receiver. As mentioned in the article below,
# some processes "alter" the real time (either increase or decrease
# it) that gettimeofday() returns, thus making it
# inaccurate. clock_gettime(CLOCK_REALTIME) or
# clock_gettime(CLOCK_MONOTONIC) should've been used. Anyway, this
# means that some of the timestamps of the packets at the receiver end
# are suspect, because they seem to have arrived even before they were
# sent (spooky!). We cannot neglect those packets because that would
# affect the picture of the channel capacity, but at the same time,
# those values present an incorrect picture of the trace because of
# the faulty recv time values. Hence we are completely removing those
# traces from our consideration.
#
# https://blog.habets.se/2010/09/gettimeofday-should-never-be-used-to-measure-time.html


# compute average one way delays
flist = glob.glob('traces/receiver_*.log')
flist.sort()
with open('trace_statistics.csv', 'w') as fout:
    fout.write('trace,delay_min_ms,delay_max_ms,delay_avg_ms,delay_std_ms,delay_25_ms,delay_50_ms,delay_75_ms,bw_min_Mbps,bw_max_Mbps,bw_avg_Mbps,bdp_bytes' + os.linesep)
    for fpath in tqdm(flist):
        tracename = os.path.basename(fpath).split('_')[1].split('.')[0]

        #table = np.loadtxt(fpath, delimiter=',', usecols=[4,5], skiprows=1)
        table = pd.read_csv(fpath, usecols=[2,3,4,5])
        table.set_index('seq', inplace=True)
        npackets = table.index.size
        if npackets == 0:
            continue

        # compute the delays
        delays = (table.time_recv - table.time_sent) * 1000 # convert to milliseconds

        # compute bw
        table['time_recv_ms'] = (table.time_recv.values * 1000).round()
        bw = table.groupby('time_recv_ms').bytes.sum()
        bw = bw.reindex(pd.RangeIndex(bw.index[0], bw.index[-1]))
        bw = (bw * 8) / 1000

        # compute bdp
        bdp = (delays.min() * bw.mean()) * 1000.0 # convert to bytes

        fout.write('{},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.0f}'.format(tracename, delays.min(), delays.max(), delays.mean(), delays.std(), delays.quantile(0.25), delays.quantile(0.5), delays.quantile(0.75), bw.min(), bw.max(), bw.mean(), bdp) + os.linesep)
