# same as runmm.py but changing the way simulation is being run

import os, sys
import signal
import argparse
import threading
import subprocess as sp

from time import sleep
from plot import plot_tput_delay, plot_tput_delay_tcpdump
from utils import *

class Simulation(object):
    PORT = 9999
    BLKSIZE_DEFAULT = 128
    TTR_DEFAULT = 10
    
    def __init__(self, trace, port=None, ttr=None, n_blks=None, filepath=None, blksize=None, cc_algo=None, buf_len=None, mm_delay=None, iperf=False):
        '''Class for running mahimahi simulations on mmwave channel traces.
        
        trace: the mmwave channel trace to use for this simulation
        
        port: the port to use (9999 by default)
        
        sending mode: only one of the three options below:
        
        -- ttr: time to run the simulation (seconds)
              
        -- n_blks: how many blocks of data to send
        
        -- filepath: trace file from which to send data
        
        blksize: size of a block of data that is sent in a single
        send() function in the sender (KiB)
        
        cc_algo: the congestion control algorithm to use
        
        buf_len: length of buffer to use in mahimahi

        mm_delay: artificial channel delay to impose 
        
        iperf: whether to use iperf or not instead of our custom
        sender/receiver

        '''
        # the trace to use to emulate the link 
        self.trace = trace
        
        self.port = port if port is not None else Simulation.PORT
        
        # packet sending mode
        self.ttr = self.n_blks = self.filepath = None
        if (ttr is not None) + (n_blks is not None) + (filepath is not None) > 1:
            raise Exception('only one of \'ttr\', \'n_blks\' and \'filepath\' may be specified')
        if n_blks is not None:
            self.n_blks = n_blks
        elif filepath is not None:
            self.filepath = filepath
        else:
            self.ttr = ttr if ttr is not None else Simulation.TTR_DEFAULT
        
        # sending block size
        self.blksize = blksize if blksize is not None else Simulation.BLKSIZE_DEFAULT
        
        # the congestion control algo
        self.cc_algo = cc_algo
        
        # length of buffer in mahimahi
        self.buf_len = buf_len

        # value of delay to give to mm-delay
        self.mm_delay = mm_delay
        
        # use iperf instead of our sender and receiver?
        self.iperf = iperf

    def run(self, savedir='output', log=False, skip_seconds=0, verbose=0, disp_plot=False, save_plot=True, suffix=None):
        '''Run the simulation with following runtime options.
        
        savedir: directory where to store outputs
        
        log: log the data transfer (useful for debugging and offline
        prediction algo)

        skip_seconds: initial amount of time to skip during parsing,
        to compute throughput and delay (useful to exclude any warmup
        phase)
        
        disp_plot: display a plot
        
        save_plot: save the plot

        '''
        
        # make output directories
        if not os.path.exists(savedir):
            os.makedirs(savedir)
        
        print('Saving all output to this directory: "{}"'.format(savedir))
        
        # fixing dest file names
        if self.ttr is not None:
            saveprefix = '{}_T{}'.format(self.trace, self.ttr)
        elif self.n_blks is not None:
            saveprefix = '{}_N{}'.format(self.trace, self.n_blks)
        else:
            assert (self.filepath is not None)
            filename = os.path.splitext(os.path.basename(self.filepath))[0]
            saveprefix = '{}_file_{}'.format(self.trace, filename)
        
        saveprefix += '_{}KiB'.format(self.blksize)
        
        if self.buf_len is not None:
            saveprefix += '_Q{}'.format(self.buf_len)

        if self.mm_delay is not None and self.mm_delay > 0:
            saveprefix += '_delay{:02d}'.format(self.mm_delay)

        if suffix is not None:
            saveprefix += '_' + suffix
        
        savepathprefix = os.path.join(savedir, saveprefix)
        
        # starting the simulations
        
        # (i) receiver command
        receiver_cmd = 'sender_receiver/receiver {} 1 {}'.format(self.port, int(verbose >= 1))
        if log:
            recvlogdir = savepathprefix + '_receiver'
            if not os.path.exists(recvlogdir):
                os.mkdir(recvlogdir)
            receiver_cmd += ' --log {}'.format(os.path.join(recvlogdir, 'recvlog'))
        
        # (ii) mm command
        tracepath = os.path.join('traces', 'channels', self.trace)
        mm_cmd = 'mm-link {0} {0} --uplink-log {1}_uplink.csv'.format(tracepath, savepathprefix)
        if self.mm_delay is not None and self.mm_delay > 0:
            mm_cmd = 'mm-delay {} '.format(self.mm_delay) + mm_cmd

        if self.buf_len is not None:
            # mm_cmd += ' --uplink-queue=droptail --uplink-queue-args=bytes={}'.format(self.buf_len)
            mm_cmd += ' --uplink-queue=droptail --uplink-queue-args=bytes={}'.format(self.buf_len)
            mm_cmd += ' --downlink-queue=droptail --downlink-queue-args=bytes={}'.format(self.buf_len)
        
        # (iii) sender command
        sender_cmd = 'sender_receiver/sender {{}} {}'.format(self.port)
        #if self.filepath is not None:
        #    sender_cmd += ' -f {}'.format(self.filepath)
        #elif self.n_blks is not None:
        #    sender_cmd += ' -n {}'.format(self.n_blks)
        #else:
        #    sender_cmd += ' -t {}'.format(self.ttr)
        sender_cmd += ' -t 305'
        if self.blksize != Simulation.BLKSIZE_DEFAULT:
            sender_cmd += ' -b {}'.format(self.blksize)
        if self.cc_algo is not None:
            sender_cmd += ' -C {}'.format(self.cc_algo)
        if log:
            sender_cmd += ' -l {}'.format(savepathprefix + '_sender.log')
        
        server_ip = '100.64.0.1' # MAHIMAHI_BASE: address exposed by native machine to processes inside mahimahi

        mmlogfpath = savepathprefix + '_uplink.csv'

        # starting the receiver in a separate process
        if verbose >= 1:
            print('Starting receiver using command:', receiver_cmd)
        
        # receiver_process = sp.Popen('sudo tcpdump -i any -s 96 -w {}_receiver.pcap & '.format(savepathprefix) + receiver_cmd, shell=True, universal_newlines=True, preexec_fn=os.setsid)
        os.system('sudo tcpdump -i any -s 96 -w {}_receiver.pcap & '.format(savepathprefix) + receiver_cmd + ' &')
        sleep(2)

        # if verbose >= 2:
        #     print('Receiver process started, pid', receiver_process.pid)

        # starting the sender and mahimahi in a separate process
        #sender_cmd = mm_cmd 
        if verbose >= 1:
            print('Starting mahimahi using command:', mm_cmd)

        sender_process = sp.Popen(mm_cmd, stdin=sp.PIPE, shell=True, universal_newlines=True)
        sleep(2)

        if verbose >= 2:
            print('Mahimahi process started, pid', sender_process.pid)

        # output = sp.check_output("ifconfig", shell=True, universal_newlines=True)
        # interface = "delay-"+output.split("delay-")[-1].split(":")[0]
        # os.system("sudo ifconfig {0} txqueuelen 10000000".format(interface))
        # sleep(1)
        # sender_process.communicate('sudo ifconfig ingress txqueuelen 10000000 &&' + sender_cmd.format(server_ip) + '& \n sleep ' + str(self.ttr) + ' \n exit')

        sender_cmd = sender_cmd.format(server_ip)
        if verbose >= 1:
            print('Starting sender process inside mahimahi using command:', sender_cmd)

        sender_process.communicate('sudo tcpdump -i any -s96 -w {}_sender.pcap & '.format(savepathprefix) + sender_cmd + ' & \n sleep ' + str(self.ttr) + ' \n exit')

        os.system('ps | pgrep -f sender_receiver/sender | xargs kill -TERM')
        os.system('ps | pgrep -f sender_receiver/receiver | xargs kill -TERM')
        os.system('ps | pgrep -f tcpdump | sudo xargs kill -TERM')
        os.system('ps | pgrep -f tcpdump | sudo xargs kill -TERM')

        # waiting for processes to close
        #if verbose >= 1:
        #    print('Waiting for sender process ...')
        #sender_process_retcode = sender_process.wait()
        #if verbose >= 2:
        #    print('Sender process returned', sender_process_retcode)
        #
        #if verbose >= 1:
        #    print('Waiting for receiver process ...')
        #receiver_process_retcode = receiver_process.wait()
        #if verbose >= 2:
        #    print('Receiver process returned', receiver_process_retcode)
            
        print('Plotting performance ...')
        #plot_tput_delay(mmlogfpath, skip_seconds=skip_seconds, title=os.path.basename(savepathprefix), disp=disp_plot, save=save_plot)
        plot_tput_delay_tcpdump('{}_sender.pcap'.format(savepathprefix), '{}_receiver.pcap'.format(savepathprefix), server_ip, mmlogfpath, skip_seconds=skip_seconds, title=os.path.basename(savepathprefix), disp=disp_plot, save=save_plot)

        os.unlink('{}_sender.pcap'.format(savepathprefix))
        os.unlink('{}_receiver.pcap'.format(savepathprefix))

        return

if __name__ == '__main__':
    ''' Interactive program to run a full simulation. '''
    
    parser = argparse.ArgumentParser(description="Run mahimahi for cellular network simulations")
    
    parser.add_argument('trace', metavar='CHANNEL_TRACE', 
                        help='Cellsim traces to be used (channel simulation; choose one from traces/channels/)')
    
    parser.add_argument('--port', '-p', type=int, 
                        help='Port number to use',
                        default=Simulation.PORT)
    
    megroup = parser.add_mutually_exclusive_group()
    
    megroup.add_argument('--ttr', '-t', metavar='DURATION_SEC', 
                         help='Duration to run the experiment (seconds)',
                         default=Simulation.TTR_DEFAULT)
    
    megroup.add_argument('--n-blocks', '-n', metavar='NUM_BLOCKS',
                         help='Number of blocks to send')
    
    megroup.add_argument('--trace-file', '-f', dest='filepath',
                         help='Trace file from which to generate traffic for sender')
    
    parser.add_argument('--blksize', '-b', type=int,
                        help='Size of a block (multiples of KiB)',
                        default=Simulation.BLKSIZE_DEFAULT)
    
    parser.add_argument('--cc-algo', '-C', 
                        choices=('cubic', 'reno', 'ccp', 'bbr'),
                        help='Congestion control algorithm to use')
    
    parser.add_argument('--buf-len', '-q', type=positive_int,
                        help='Buffer size in mahimahi (bytes)')

    parser.add_argument('--mm-delay', type=unsigned_int,
                        help='Delay for mahimahi delay shell (mm-delay)')
    
    parser.add_argument('--iperf', action='store_true',
                        help='Use iperf for the test',
                        default=False)

    # runtime options
    parser.add_argument('--dir', '-d', 
                        help='Directory to store outputs',
                        default='output')
    
    parser.add_argument('--log', '-l', action='store_true',
                        help='Log packets at the sender and receiver',
                        default=False)

    parser.add_argument('--skip-seconds', type=unsigned_int, 
                        help='Skip initial seconds before computing performance (default: 0)',
                        default=0)
    
    parser.add_argument('--verbose', '-v', action='count',
                        help='Show verbose output',
                        default=0)

    parser.add_argument('--disp-plot', action='store_true',
                        help='Display the tput-delay plot',
                        default=True)

    parser.add_argument('--save-plot', action='store_true',
                        help='Save the tput-delay plot',
                        default=False)
    
    args = parser.parse_args()

    prettyprint_args(args)
    
    sim = Simulation(args.trace, args.port, args.ttr, args.n_blocks, args.filepath, args.blksize, args.cc_algo, args.buf_len, args.mm_delay, args.iperf)
    
    sim.run(args.dir, args.log, args.skip_seconds, args.verbose, args.disp_plot, args.save_plot)
    
    print("Finished")
