from subprocess import Popen, PIPE, call
# import arg_parser
from argparse import ArgumentParser
from multiprocessing import Process
import signal
import subprocess
import sys
import os
import threading
from time import sleep, time
# import context
import threading
from tqdm import tqdm

def positive_int(arg):
        arg = int(arg)
        if arg <= 0:
                raise argparse.ArgumentError('Argument must be a positive integer')
        return arg

def simpleRun():
	print args
	
	if args.algo == 'verus':
		RunVERUS()
	elif args.algo == 'copa':
		RunCopa()
	print ("Finished")

	return

def RunVERUS():
	if not os.path.exists(args.dir + '/output_verus'):
		os.makedirs(args.dir+ "/output_verus")
	if not os.path.exists(args.dir + '/output_verus/'+str(args.name)):
		os.makedirs(args.dir+ "/output_verus/"+str(args.name))
	
	print("Begin " + str(args.time) + " seconds of verus transmission")
	command = "./verus_protocol/verus/src/verus_server -name "+args.dir + "/output_verus/"+str(args.name)+" -p 60001 -t "+ str(args.time)#+" > rubbishVerus"
	print command
	pro = Popen(command, stdout=PIPE, shell=True, preexec_fn=os.setsid)
	# tracepath = os.path.join('traces', 'channels', args.trace)
	# saveprefix = '{}_T{}'.format(args.trace, args.time)
	# tmp = "mm-link ./"+str(args.trace)+" ./"+str(args.trace)+"--uplink-log "+str(args.dir)+"/output_verus/"+args.name+"-uplink.csv --downlink-log "+str(args.dir)+"/verus/"+str(args.name)+"/"+args.name+"-downlink.csv"
	tmp= "mm-link ./"+str(args.trace)+" ./"+str(args.trace)+ " --meter-all --uplink-log "+str(args.dir)+"/output_verus/"+str(args.name)+"/"+args.name+"_uplink.csv --downlink-log "+str(args.dir)+"/output_verus/"+str(args.name)+"/"+args.name+"_downlink.csv --uplink-queue=droptail --uplink-queue-args=bytes={}".format(args.queue)
	p = Popen(tmp, stdin=PIPE,shell=True)
	p.communicate("./verus_protocol/verus/src/verus_client $MAHIMAHI_BASE -p 60001\nexit\n")

	os.system("ps | pgrep -f verus_server | xargs kill -9")
	os.system("ps | pgrep -f verus_client | xargs kill -9")
	os.system("mv client_60001* "+args.dir+"/output_verus/"+str(args.name)+"/")
	sleep(5)



if __name__ == '__main__':
	parser = ArgumentParser(description="Shallow queue tests")
	parser.add_argument('--dir', '-d',help="Directory to store outputs",required=True)
	parser.add_argument('--trace', '-tr',help="Cellsim traces to be used",required=True)
	parser.add_argument('--time', '-t',help="Duration (sec) to run the experiment",type=int,default=10)
	parser.add_argument('--name', '-n',help="name of the experiment",required=True)
	parser.add_argument('--algo',help="Algorithm under which we are running the simulation",required=True)
	parser.add_argument('--tcp_probe',help="whether tcp probe should be run or not",action='store_true',default=False)
	parser.add_argument('--command', '-c', help="mm-link command to run", required=False)                
	parser.add_argument('--queue', '-q', type=positive_int, help='Buffer size in mahimahi (bytes)')
	args = parser.parse_args()
	simpleRun()