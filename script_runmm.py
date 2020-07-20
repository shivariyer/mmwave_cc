# batch running of experiments

import os
import argparse

from runmm import Simulation, positive_int, unsigned_int

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    megroup = parser.add_mutually_exclusive_group()
    parser.add_argument('savedir', help='Directory to store outputs')
    megroup.add_argument('--ttr', '-t', type=positive_int, metavar='DURATION_SEC', 
                         help='Duration to run the experiment (seconds)')
    megroup.add_argument('--n-blocks', '-n', type=positive_int, metavar='NUM_BLOCKS',
                         help='Number of blocks to send')
    megroup.add_argument('--trace-file', '-f', dest='filepath',
                         help='Trace file from which to generate traffic for sender')
    parser.add_argument('--blksize', '-b', type=int,
                        help='Size of a block (multiples of KiB)',
                        default=Simulation.BLKSIZE_DEFAULT)
    parser.add_argument('--cc-algo', '-C', help='CC algo to use')
    parser.add_argument('--log', '-l', action='store_true',
                        help='Log packets at the sender and receiver',
                        default=False)
    parser.add_argument('--verbose', '-v', action='count',
                        help='Show verbose output',
                        default=0)
    args = parser.parse_args()
    
    port = 9999

    trace_list = ['humanmotion', 'walkandturn', 'fanrunning', 'stationary']
    bdp_bits_list = [492986.66, 2228554.3, 187462.8, 2408384]
    bdp_bytes_list = [61623.3325225, 278569.2875, 23432.85, 301048] # approximate values of BDP
    
    #buf_len_list = [300000, 500000, 400000, 500000]
    buf_len_list_1 = [ 60000, 300000, 25000, 300000] # approximations of BDPs
    buf_len_list_2 = [120000, 600000, 50000, 600000] # 2BDP
    buf_len_list_3 = [ 30000, 150000, 12500, 150000] # 0.5BDP

    trace_list = 3 * trace_list
    buf_len_list = buf_len_list_1 + buf_len_list_2 + buf_len_list_3

    for trace, buf_len in zip(trace_list, buf_len_list):
        
        print('**** Trace: {}, Buffer size: {} bytes ****'.format(trace, buf_len))
        
        sim = Simulation(trace, port, args.ttr, args.n_blocks, args.filepath, args.blksize, args.cc_algo, buf_len)
        sim.run(args.savedir, log=args.log, verbose=args.verbose)
