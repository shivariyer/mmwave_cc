import os
import argparse
import numpy as np


def gen_trace(send_rate, duration=60, probe=None, seed=None, savedir=os.path.join('traces', 'background')):
    np.random.seed(seed)

    # number of packets in 60 seconds
    num_packets = int(float(send_rate) * 5000 * duration / 60.0)
    lamb = 1000.0 * duration/float(num_packets)
    print(lamb)
    ts_list = np.cumsum(np.random.poisson(lamb, num_packets))
    if probe is None:
        ts_list_copy = ts_list
        trace_path = os.path.join(savedir, '{}Mbps-T{}-seed{}.trace'.format(send_rate, duration, seed))
    else:
        probe_interval = float(probe[0])
        probe_length = int(probe[1])
        
        # adding spikes
        ts_list_copy = []
        probe_point = probe_interval
        for ele in ts_list:
            if ele >= probe_point:
                    ts_list_copy.extend(['{}*'.format(int(probe_point))] * probe_length)
                    probe_point += probe_interval
            ts_list_copy.append(str(ele))
    
        trace_path = os.path.join(savedir, '{}Mbps-T{}-bint{}-blen{}-seed{}.trace'.format(send_rate, probe[0], probe[1], duration, seed))

    if not os.path.exists(savedir):
        os.makedirs(savedir)
    
    # write timestamps to trace
    with open(trace_path, 'w') as trace:
        for ts in ts_list_copy:
            trace.write('%s\n' % ts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Generate trace files for generating TCP traffic for our experiments')
    parser.add_argument('rate', metavar='RATE_Mbps',
                        help='Rate at which to generate packets (Mbps)')
    parser.add_argument('--duration', type=int, default=60,
                        help='Duration of trace (in seconds)')
    parser.add_argument('--probe', metavar=('PROBE_INTERVAL', 'PROBE_LENGTH'), nargs=2,
                        help='Send probe packets given, 1) interval between probes (ms), 2) length of a probe (packets)')
    parser.add_argument('--seed', type=int, default=0,
                        help='Random seed')
    parser.add_argument('--output-dir', '-of', metavar='SAVE_DIR', default=os.path.join('traces', 'background'), 
                        help='Location to save generated traces')
    args = parser.parse_args()
    
    gen_trace(args.rate, args.duration, args.probe, args.seed, args.output_dir)
