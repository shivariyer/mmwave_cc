import os, sys
import signal
import argparse
import threading
import subprocess

from time import sleep

def RunSim():
    server_ip = "100.64.0.1" # MAHIMAHI_BASE: address exposed by native machine to process inside mahimahii 
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
    
    # starting the server receiver in a separate process
    recvlogfpathprefix = os.path.join(args.dir, saveprefix + '_receiver')
    receiver_cmd = 'sender_receiver/receiver {} {} 1'.format(args.port, recvlogfpathprefix) # removed "&"
    print('Receiver run using command:', receiver_cmd)
    receiver_process = subprocess.Popen(receiver_cmd.split()) # shell=True
    print('Receiver started, pid', receiver_process.pid)
    
    # starting the mahimahi router in a separate process
    mm_cmd = "mm-link traces/channels/{0} traces/channels/{0} --uplink-log {1}/{2}_uplink.csv --downlink-log {1}/{2}_downlink.csv".format(args.trace, args.dir, saveprefix)
    if args.queue is not None:
        mm_cmd += " --uplink-queue=droptail --uplink-queue-args=bytes={}".format(args.queue)
    
    print('Mahimahi run using command:', mm_cmd)
    mm_process = subprocess.Popen(mm_cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True) # shell=True # add text=True if required (may be required in more recent python3 versions such as python 3.7.x
    
    # to ensure the mm interface gets up
    sleep(5)
    
    print('Mahimahi process started, pid', mm_process.pid)
    
    # starting the user sender
    senderlogfpath = os.path.join(args.dir, saveprefix + '_sender.log')
    sender_cmd = 'sender_receiver/sender {} {} {} {} --type '.format(server_ip, args.port, ttr, senderlogfpath)
    if args.const is not None:
        sender_cmd += 'const {} {}'.format(args.const[0], args.const[1])
    elif args.filepath is not None:
        sender_cmd += 'file ' + args.filepath
    
    print(sender_cmd)
    stdout, _ = mm_process.communicate(sender_cmd)
    print('mm_process.communicate() has returned.')
    print('stdout:', stdout)
    
    # sleep(args.time)
    
    # waiting for processes to close
    
    print('Waiting for mahimahi to close.')
    print('Mahimahi process returned', mm_process.wait())
    print('Done!')
    
    print('Waiting for server process to close.')
    receiver_process.send_signal(signal.SIGINT)
    print('Server process returned', receiver_process.wait())
    print('Done!')
    
    # subprocess.call("sudo pkill sender_sender", shell=True)
    # subprocess.call("sudo pkill -INT server_receiver", shell=True)
    
    return


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
    
    args = parser.parse_args()
    
    # make output directories
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
        
    RunSim()
    
    print("Finished")
