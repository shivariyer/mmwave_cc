#!/usr/bin/env python

import os
import argparse
import numpy as np
from os import path
#from helpers import make_sure_path_exists


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bandwidth', '-bw', metavar='Mbps', required=True,
                        help='constant bandwidth (Mbps)')
    parser.add_argument('--output-dir', '-of', metavar='DIR', required=True,
                        help='directory to output trace')
    parser.add_argument('--burst', metavar=('BURST_INTERVAL', 'BURST_LENGTH'), nargs=2,
                        help='2 parameters, 1) interval between bursts (ms), 2) length of burst')
    parser.add_argument('--duration', type=int, default=60, help='Duration of trace (in seconds)')
    parser.add_argument('--seed', type=int, default=0, help='Random seed')
    args = parser.parse_args()
    
    np.random.seed(args.seed)

    # number of packets in 60 seconds
    num_packets = int(float(args.bandwidth) * 5000 * args.duration / 60.0)
    lamb = 1000.0 * args.duration/float(num_packets)
    print(lamb)
    ts_list = np.cumsum(np.random.poisson(lamb,num_packets))

    if args.burst is None:
        ts_list_copy = ts_list
        trace_path = path.join(args.output_dir, '{}mbps-T{}-seed{}.trace'.format(args.bandwidth, args.duration, args.seed))
    else:
        burst_interval = float(args.burst[0])
        burst_length = int(args.burst[1])
        
        # adding spikes
        ts_list_copy = []
        burst_point = burst_interval
        for ele in ts_list:
            if ele >= burst_point:
                    ts_list_copy.extend(['{}*'.format(int(burst_point))] * burst_length)
                    burst_point += burst_interval
            ts_list_copy.append(str(ele))
    
        trace_path = path.join(args.output_dir, '{}mbps-bint{}-blen{}-T{}-seed{}.trace'.format(args.bandwidth, args.burst[0], args.burst[1], args.duration, args.seed))

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # write timestamps to trace
    with open(trace_path, 'w') as trace:
        for ts in ts_list_copy:
            trace.write('%s\n' % ts)


if __name__ == '__main__':
    main()
