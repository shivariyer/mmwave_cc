
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# arg expected is the sender log (sender_xxx.log)
logfilepath_sent = sys.argv[1]
logfilepath_recv = logfilepath_sent.replace('sender', 'receiver')
logfilepath_rt = logfilepath_sent.replace('sender', 'roundtrip')
dirpath = os.path.dirname(logfilepath_sent)
tracename = os.path.basename(logfilepath_sent).split('_')[1].split('.')[0]

# sent throughput
sent = pd.read_csv(logfilepath_sent, skiprows=1, usecols=[0,1,2])
sent.set_index('seq', inplace=True)
npackets_sent = sent.index.size
sent['time_sent_ms'] = (sent.time_sent.values * 1000).round()
bw_sent = sent.groupby('time_sent_ms').bytes.sum()
bw_sent = bw_sent.reindex(pd.RangeIndex(bw_sent.index[0], bw_sent.index[-1]))
bw_sent = (bw_sent * 8) / 1000
ax = bw_sent.plot(label='Throughput sent (avg = {:.2f} Mbps)'.format(bw_sent.mean()))
print('Avg sent throughput: {:.2f} Mbps'.format(bw_sent.mean()))

# recved throughput
recv = pd.read_csv(logfilepath_recv, usecols=[2,3,5])
recv.set_index('seq', inplace=True)
npackets_recv = recv.index.size
recv['time_recv_ms'] = (recv.time_recv.values * 1000).round()
bw_recv = recv.groupby('time_recv_ms').bytes.sum()
bw_recv = bw_recv.reindex(pd.RangeIndex(bw_recv.index[0], bw_recv.index[-1]))
bw_recv = (bw_recv * 8) / 1000
bw_recv.plot(ax=ax, label='Throughput received (avg = {:.2f} Mbps)'.format(bw_recv.mean()))
print(os.linesep + 'Avg recv throughput: {:.2f} Mbps'.format(bw_recv.mean()))
print('Recv packets lost: {:.2f}% ({}/{})'.format((npackets_sent - npackets_recv)*100.0/npackets_sent, npackets_recv, npackets_sent))

# roundtrip received data
rt = pd.read_csv(logfilepath_rt, skiprows=1, usecols=[0,1,4])
rt.set_index('seq', inplace=True)
npackets_rt = rt.index.size
rt['time_rt_ms'] = (rt.time_rt.values * 1000).round()
bw_rt = rt.groupby('time_rt_ms').bytes.sum()
bw_rt = bw_rt.reindex(pd.RangeIndex(bw_rt.index[0], bw_rt.index[-1]))
bw_rt = (bw_rt * 8) / 1000
bw_rt.plot(ax=ax, label='Throughput roundtrip (avg = {:.2f} Mbps)'.format(bw_rt.mean()))
print(os.linesep + 'Avg rt throughput: {:.2f} Mbps'.format(bw_rt.mean()))
print('Roundtrip packets lost: {:.2f}% ({}/{})'.format((npackets_sent - npackets_rt)*100.0/npackets_sent, npackets_rt, npackets_sent))

ax.legend(loc=0)
ax.set_title(tracename)
ax.set_xlabel('Timestamp (Milliseconds since Epoch)')
ax.set_ylabel('Kb/ms = Mbps')

plt.savefig(os.path.join(dirpath, tracename + '_bw.pdf'))

plt.show()

# now save the trace
trace1 = (recv.time_recv_ms.values - recv.time_recv_ms.iloc[0] + 1).astype(int)
np.savetxt(os.path.join(dirpath, tracename + '.trace1'), trace1, fmt='%d')

trace2 = np.vstack((np.arange(trace1[-1] + 1), np.bincount(trace1)))
trace2 = trace2[:, trace2[1,:] != 0]
np.savetxt(os.path.join(dirpath, tracename + '.trace2'), trace2.T, fmt='%d')
