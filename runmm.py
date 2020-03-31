#from __future__ import print_function

import os, sys
import signal
import argparse
import threading
import subprocess

from time import sleep
from plot import plot_tput_delay

def RunSim():
    server_ip = "100.64.0.1" # MAHIMAHI_BASE: address exposed by native machine to processes inside mahimahi
    server_reverse_ip = "100.64.0.2" # address exposed by mahimahi to processes outside
        
    if args.const is not None:
        saveprefix = '{}_const_{}_{}'.format(args.trace, args.const[0], args.const[1])
    elif args.filepath is not None:
        filename = os.path.splitext(os.path.basename(args.filepath))[0]
        saveprefix = '{}_file_{}'.format(args.trace, filename)
    
    if args.queue is not None:
        saveprefix += '_q{}'.format(args.queue)
    
    savepathprefix = os.path.join(args.dir, saveprefix)
    
    # (1) starting the server receiver in a separate process inside a mahimahi shell
    receiver_cmd = ' -- sender_receiver/receiver {} {} {:d}'.format(args.port, args.maxflows, args.verbose) # removed "&"
    if args.recvlog:
        recvlogdir = savepathprefix + '_receiver'
        if not os.path.exists(recvlogdir):
            os.mkdir(recvlogdir)
        receiver_cmd += ' --log {}'.format(os.path.join(recvlogdir, 'recvlog'))
    
    tracepath = os.path.join('traces', 'channels', args.trace)
    mm_cmd = "mm-link {0} {0} --uplink-log {1}_uplink.csv --downlink-log {1}_downlink.csv".format(tracepath, savepathprefix)
    if args.queue is not None:
        mm_cmd += " --uplink-queue=droptail --uplink-queue-args=bytes={}".format(args.queue)
    
    mm_cmd += receiver_cmd
    print('Starting receiver inside Mahimahi using command:', mm_cmd)
    #mm_process = subprocess.Popen(mm_cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    mm_process = subprocess.Popen(mm_cmd.split(), universal_newlines=True)
    
    # to ensure the mm interface gets up
    print('Waiting for mm-interface to get up ...')
    sleep(1)
    
    print('Mahimahi process started, pid', mm_process.pid)
    
    # starting the mahimahi router in a separate process
    
    # starting the user sender
    senderlogfpath = savepathprefix + '_sender.log'
    sender_cmd = 'sender_receiver/sender {} {} {} --type '.format(server_reverse_ip, args.port, senderlogfpath)
    if args.const is not None:
        sender_cmd += 'const {} {}'.format(args.const[0], args.const[1])
    elif args.filepath is not None:
        sender_cmd += 'file ' + args.filepath
        sender_cmd += ' --maxflows {}'.format(args.maxflows)
    
    print('Starting sender using command:', sender_cmd)
    sender_process = subprocess.Popen(sender_cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    #sender_process = subprocess.Popen(sender_cmd.split())
    print('Sender started, pid', sender_process.pid)
    
    # waiting for processes to close
    
    print('Waiting for sender process ...')
    print('Sender process returned', sender_process.wait())
    
    print('Waiting for receiver process ...')
    print('Mahimahi process returned', mm_process.wait())
    
    print('Plotting performance ...')
    plot_tput_delay(savepathprefix + '_downlink.csv', title=os.path.basename(savepathprefix), disp=True, save=True)
    
    print('Done!')
    
    return


def unsigned_int(arg):
    arg = int(arg)
    if arg < 0:
        raise argparse.ArgumentError('Argument must be a nonnegative integer')
    return arg


def positive_int(arg):
    arg = int(arg)
    if arg <= 0:
        raise argparse.ArgumentError('Argument must be a positive integer')
    return arg


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="Run mahimahi for cellular network simulations")
    
    parser.add_argument('trace', metavar='CHANNEL_TRACE', 
                        help='Cellsim traces to be used (channel simulation; choose one from traces/channels/)')
    
    parser.add_argument('--port', '-p', type=int, 
                        help='Port number to use',
                        default=9999)
    
    parser.add_argument('--dir', '-d', 
                        help='Directory to store outputs',
                        default='output')
    
    parser.add_argument('--queue', type=positive_int,
                        help='Queue size in mahimahi (bytes)')
    
    megroup = parser.add_mutually_exclusive_group()
    
    megroup.add_argument('--const', nargs=2, metavar=('NUM_PACKETS', 'PROBE_MODE'),
                         help='A single flow with specified number of packets. Probe mode is 0 (test cc) or 1 (default cc).')
    
    megroup.add_argument('--time-rate', '-t', nargs=2, metavar=('DURATION_SEC', 'BW_MiBps'), 
                        help='Duration (sec) to run the experiment with sending rate (# bytes per second)')
    
    megroup.add_argument('--file', '-f', dest='filepath',
                         help='File from which to generate user sender trace')
    
    parser.add_argument('--maxflows', type=unsigned_int,
                        help='Limit on number of flows in the simulation (0 for unlimited)',
                        default=1)
    
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Log progress on console',
                        default=False)
    
    parser.add_argument('--recvlog', action='store_true',
                        help='Log packets at the receiver',
                        default=False)
    
    args = parser.parse_args()
    
    if args.time_rate is not None:
        raise argparse.ArgumentError('\"--time-rate\" is not implemented for now.')
    
    # make output directories
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    
    RunSim()
    
    print("Finished")
