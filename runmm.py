from __future__ import print_function

import os, sys
import signal
import argparse
import threading
import subprocess

from time import sleep

def RunSim():
    server_ip = "100.64.0.1" # MAHIMAHI_BASE: address exposed by native machine to process inside mahimahii
    server_reverse_ip = "100.64.0.2" # address exposed by mahimahi to process outsidexs
    #server_ip = args.servAddr
    #port = '5999'
    #mtu_bytes = '1500'
    #bw_mbps = args.bandwidth
    ttr = str(args.time)
    probe = 1
    
    if args.const is not None:
        saveprefix = '{}_const_{}_{}'.format(args.trace, args.const[0], args.const[1])
    elif args.filepath is not None:
        filename = os.path.splitext(os.path.basename(args.filepath))[0]
        saveprefix = '{}_file_{}'.format(args.trace, filename)
    
    if args.queue is not None:
        saveprefix += '_q{}'.format(args.queue)
    
    # (1) starting the server receiver in a separate process inside a mahimahi shell
    receiver_cmd = ' -- sender_receiver/receiver {} {} {}'.format(args.port, args.maxflows, args.verbose) # removed "&"
    if args.recvlog:
        recvlogdir = os.path.join(args.dir, saveprefix + '_receiver')
        if not os.path.exists(recvlogdir):
            os.mkdir(recvlogdir)
        recvlogfpathprefix = os.path.join(recvlogdir, 'recvlog')
        receiver_cmd += ' --log {}'.format(recvlogfpathprefix)
    #print('Receiver run using command:', receiver_cmd)
    
    mm_cmd = "mm-link traces/channels/{0} traces/channels/{0} --uplink-log {1}/{2}_uplink.csv --downlink-log {1}/{2}_downlink.csv".format(args.trace, args.dir, saveprefix)
    if args.queue is not None:
        mm_cmd += " --uplink-queue=droptail --uplink-queue-args=bytes={}".format(args.queue)
    
    mm_cmd += receiver_cmd
    print('Starting receiver inside Mahimahi using command:', mm_cmd)
    mm_process = subprocess.Popen(mm_cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    #mm_process = subprocess.Popen(mm_cmd.split(), universal_newlines=True)
    
    # to ensure the mm interface gets up
    print('Waiting for mm-interface to get up ...')
    sleep(1)
    
    print('Mahimahi process started, pid', mm_process.pid)
    
    #receiver_process = subprocess.Popen(receiver_cmd.split()) # shell=True
    #print('Receiver started, pid', receiver_process.pid)
    
    # starting the mahimahi router in a separate process
    
    # starting the user sender
    senderlogfpath = os.path.join(args.dir, saveprefix + '_sender.log')
    sender_cmd = 'sender_receiver/sender {} {} {} {} --type '.format(server_reverse_ip, args.port, ttr, senderlogfpath)
    if args.const is not None:
        sender_cmd += 'const {} {}'.format(args.const[0], args.const[1])
    elif args.filepath is not None:
        sender_cmd += 'file ' + args.filepath
        sender_cmd += ' --maxflows {}'.format(args.maxflows)
    
    #print(sender_cmd)
    #stdout, _ = mm_process.communicate(sender_cmd)
    #print('mm_process.communicate() has returned.')
    #print('stdout:', stdout)
    
    print('Starting sender using command:', sender_cmd)
    sender_process = subprocess.Popen(sender_cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    #sender_process = subprocess.Popen(sender_cmd.split())
    print('Sender started, pid', sender_process.pid)
    
    # sleep(args.time)
    #sleep(5)
    
    # waiting for processes to close

    print('Waiting for sender process ...')
    print('Sender process returned', sender_process.wait())
    
    print('Waiting for receiver process ...')
    #mm_process.send_signal(signal.SIGINT)
    print('Mahimahi process returned', mm_process.wait())
    
    # print('Waiting for server process to close.')
    # receiver_process.send_signal(signal.SIGINT)
    # print('Server process returned', receiver_process.wait())
    # print('Done!')
    
    # subprocess.call("sudo pkill sender_sender", shell=True)
    # subprocess.call("sudo pkill -INT server_receiver", shell=True)
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
    
    # parser.add_argument('--servaddr', '-sa',
    #     		help="Server address, make it match with a local interface different from localhost",
    #     		required=True)

    parser.add_argument('--port',
                        help='Port number to use',
                        required=True)
    
    parser.add_argument('--trace', '-tr',
			help='Cellsim traces to be used (channel simulation; choose one from traces/channels/)',
			required=True)
    
    parser.add_argument('--dir', '-d',
			help="Directory to store outputs",
			default='output')
    
    parser.add_argument('--time', '-t',
			help="Duration (sec) to run the experiment",
			type=int,
			default=10)
    
    parser.add_argument('--bandwidth', '-bw',
			help='Bandwidth in MiBps',
			default='13')
    
    parser.add_argument('--queue', type=positive_int, help='Queue size in mahimahi (bytes)')

    megroup = parser.add_mutually_exclusive_group()

    megroup.add_argument('--const', nargs=2,
                         metavar=('NUM_PACKETS', 'PROBE_MODE'))
        
    megroup.add_argument('--file', '-f',
                         dest='filepath',
                         help="File from which to generate user sender trace")

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
    
    # make output directories
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
        
    RunSim()
    
    print("Finished")
