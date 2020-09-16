import os, sys
import signal
import argparse
import threading
import subprocess as sp

from time import sleep
from plot import plot_tput_delay


class Simulation(object):
    PORT = 9999
    BLKSIZE_DEFAULT = 128
    TTR_DEFAULT = 10
    
    def __init__(self, trace, port=None, n_senders=1, ttr=None, n_blks=None, filepath=None, blksize=None, cc_algo=None, buf_len=None, iperf=False):
        '''
        Class for running mahimahi simulations on mmwave channel traces.
        
        trace: the mmwave channel trace to use for this simulation
        
        port: the port to use (9999 by default)

        n_senders: number of senders (1 by default)
        
        sending mode: only one of the three options below:
        
        -- ttr: time to run the simulation (seconds)
              
        -- n_blks: how many blocks of data to send
        
        -- filepath: trace file from which to send data
        
        blksize: size of a block of data that is sent in a single send() function in the sender (KiB)
        
        cc_algo: the congestion control algorithm to use
        
        buf_len: length of buffer to use in mahimahi
        
        iperf: whether to use iperf or not instead of our custom sender/receiver
        
        '''
        # the trace to use to emulate the link 
        self.trace = trace
        
        self.port = port if port is not None else Simulation.PORT

        self.n_senders = n_senders
        
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
        
        # use iperf instead of our sender and receiver?
        self.iperf = iperf
    
    
    def run(self, savedir='output', mm_side='receiver', log=False, verbose=0, disp_plot=False, save_plot=True):
        ''' Run the simulation with following runtime options.
        
        savedir: directory where to store outputs
        
        mm_side: the side that should run inside a mahimahi shell, 'sender' or 'receiver' 
        (this is automatically set to 'receiver' when n_senders > 1)
        
        log: log the data transfer (useful for debugging and offline prediction algo)
        
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
        # mm_cmd = 'mm-link {0} {0} --uplink-log {1}_uplink.csv --downlink-log {1}_downlink.csv'.format(tracepath, savepathprefix)
        if mm_side== "receiver":
            mm_cmd = 'mm-link {0} {0} --downlink-log {1}_downlink.csv'.format(tracepath, savepathprefix)
        else:
            mm_cmd = 'mm-link {0} {0} --uplink-log {1}_uplink.csv'.format(tracepath, savepathprefix)

        if self.buf_len is not None:
            # mm_cmd += ' --uplink-queue=droptail --uplink-queue-args=bytes={}'.format(self.buf_len)
            mm_cmd += ' --uplink-queue=droptail --uplink-queue-args=bytes={}'.format(self.buf_len)
            mm_cmd += ' --downlink-queue=droptail --downlink-queue-args=bytes={}'.format(self.buf_len)
        
        # (iii) sender command
        sender_cmd = 'sender_receiver/sender {{}} {}'.format(self.port)
        if self.filepath is not None:
            sender_cmd += ' -f {}'.format(self.filepath)
        elif self.n_blks is not None:
            sender_cmd += ' -n {}'.format(self.n_blks)
        else:
            sender_cmd += ' -t {}'.format(self.ttr)
        if self.blksize != Simulation.BLKSIZE_DEFAULT:
            sender_cmd += ' -b {}'.format(self.blksize)
        if self.cc_algo is not None:
            sender_cmd += ' -C {}'.format(self.cc_algo)
        if log:
            sender_cmd += ' -l {}'.format(savepathprefix + '_sender.log')

        # when there are multiple senders, they all have to use the
        # same channel. That's why we switch over to receiver side to
        # emulate the channel.
        if self.n_senders > 1 and mm_side == 'sender':
            if verbose >= 1:
                print('Warning: Switching to mm_side receiver since n_senders > 1')
            mm_side = 'receiver'
        
        if mm_side == 'sender':
            server_ip = '100.64.0.1' # MAHIMAHI_BASE: address exposed by native machine to processes inside mahimahi

            mmlogfpath = savepathprefix + '_uplink.csv'
            
            # starting the receiver in a separate process
            if verbose >= 1:
                print('Starting receiver using command:', receiver_cmd)
            if verbose >= 2:
                receiver_process = sp.Popen(receiver_cmd.split(), universal_newlines=True)
            else:
                receiver_process = sp.Popen(receiver_cmd.split(), stdin=sp.PIPE, stdout=sp.PIPE, universal_newlines=True)
            
            if verbose >= 2:
                print('Receiver process started, pid', receiver_process.pid)
            
            # starting the sender and mahimahi in a separate process
            sender_cmd = mm_cmd + ' -- ' + sender_cmd.format(server_ip)
            if verbose >= 1:
                print('Starting sender inside mahimahi using command:', sender_cmd)
            if verbose >= 2:
                sender_process = sp.Popen(sender_cmd.split(), universal_newlines=True)
            else:
                sender_process = sp.Popen(sender_cmd.split(), stdin=sp.PIPE, stdout=sp.PIPE, universal_newlines=True)
            
            if verbose >= 2:
                print('Sender process started, pid', sender_process.pid)
            
            # waiting for sender to finish
            if verbose >= 1:
                print('Waiting for sender process ...')
            sender_process_retcode = sender_process.wait()
            if verbose >= 2:
                print('Sender process returned', sender_process_retcode)

        elif mm_side == 'receiver':
            server_ip = '100.64.0.2' # address exposed by mahimahi to processes outside

            mmlogfpath = savepathprefix + '_downlink.csv'
            
            # starting the receiver and mahimahi in a separate process
            receiver_cmd = mm_cmd + ' -- ' + receiver_cmd
            if verbose >= 1:
                print('Starting receiver inside Mahimahi using command:', receiver_cmd)
            if verbose >= 2:
                receiver_process = sp.Popen(receiver_cmd.split(), universal_newlines=True)
            else:
                receiver_process = sp.Popen(receiver_cmd.split(), stdin=sp.PIPE, stdout=sp.PIPE, universal_newlines=True)
            
            # to ensure the mm interface gets up
            if verbose >= 2:
                print('Waiting for mm-interface to get up ...')
            sleep(1)
            
            if verbose >= 2:
                print('Receiver process started, pid', receiver_process.pid)
            
            # starting the sender
            sender_cmd = sender_cmd.format(server_ip)
            if verbose >= 1:
                print('Starting {} senders using command:'.format(self.n_senders), sender_cmd)
            sender_process_list = []
            for ii in range(self.n_senders):
                if verbose >= 2:
                    sender_process = sp.Popen(sender_cmd.split())
                else:
                    sender_process = sp.Popen(sender_cmd.split(), stdin=sp.PIPE, stdout=sp.PIPE)

                sender_process_list.append(sender_process)

                if verbose >= 2:
                    print('Sender {} started, pid'.format(ii+1), sender_process.pid)
            
            # waiting for all senders to finish
            if verbose >= 1:
                print('Waiting for all senders to finish ...')

            for ii, sender_process in enumerate(sender_process_list, 1):
                sender_process_retcode = sender_process.wait()
                if verbose >= 2:
                    print('Sender process {}/{} returned'.format(ii, len(sender_process_list)), sender_process_retcode)

        else:
            raise Exception('mm_side option should be \'sender\' or \'receiver\' only')
        
        # waiting for receiver process to close
        if verbose >= 1:
            print('Waiting for receiver process ...')
        receiver_process_retcode = receiver_process.wait()
        if verbose >= 2:
            print('Receiver process returned', receiver_process_retcode)
            
        print('Plotting performance ...')
        plot_tput_delay(mmlogfpath, title=os.path.basename(savepathprefix), disp=disp_plot, save=save_plot)
        
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

def prettyprint_args(ns):
    print(os.linesep + 'Input arguments -- ')
    
    for k,v in ns.__dict__.items():
        print('{}: {}'.format(k,v))

    print()
    return


if __name__ == '__main__':
    ''' Interactive program to run a full simulation. '''
    
    parser = argparse.ArgumentParser(description="Run mahimahi for cellular network simulations")
    
    parser.add_argument('trace', metavar='CHANNEL_TRACE', 
                        help='Cellsim traces to be used (channel simulation; choose one from traces/channels/)')
    
    parser.add_argument('--port', '-p', type=int, 
                        help='Port number to use',
                        default=Simulation.PORT)

    parser.add_argument('--num-senders', '-N', type=int,
                        help='Number of senders',
                        default=1)
    
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
    
    parser.add_argument('--iperf', action='store_true',
                        help='Use iperf for the test',
                        default=False)

    # runtime options
    parser.add_argument('--dir', '-d', 
                        help='Directory to store outputs',
                        default='output')
    
    parser.add_argument('--mm-side', choices=('receiver', 'sender'),
                        help='Which side should mahimahi be run?',
                        default='receiver')
    
    parser.add_argument('--log', '-l', action='store_true',
                        help='Log packets at the sender and receiver',
                        default=True)
    
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
    
    sim = Simulation(args.trace, args.port, args.num_senders, args.ttr, args.n_blocks, args.filepath, args.blksize, args.cc_algo, args.buf_len, args.iperf)
    
    sim.run(args.dir, args.mm_side, args.log, args.verbose, args.disp_plot, args.save_plot)
    
    print("Finished")
