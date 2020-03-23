#!/bin/bash

# run emulation on mahimahi for list of user sender traces

# tr=fan_running5
odir=output/$1
seed=0
port=9999

chtrace1=fanrunning
qsize1=400000

chtrace2=humanmotion
qsize2=300000

chtrace3=stationary
qsize3=500000

chtrace4=walkandturn
qsize4=500000

let maxflows=10

# single flow with constant no of packets
#for npkts in 1000 10000 100000;
for npkts in 10000;
do
    # repeat a few times in order for ensuring correct statistical interpretations of results
    for ((flowcount = 1; flowcount <= $maxflows; flowcount++));
    do
	echo
	echo "*** Flow count" $flowcount "***"
	echo
	
    	# run mahimahi for generating packet traces, compute
    	# congestion markers and packet delays (using uplink packet
    	# traces only), using max throughput for computing bdp for
    	# queue size
	
    	# fanrunning (== fan_running5)
    	echo python runmm.py $chtrace1 -p $port -d ${odir}/_$flowcount --const $npkts 0 --queue $qsize1 --recvlog
    	python runmm.py $chtrace1 -p $port -d ${odir}/_$flowcount --const $npkts 0 --queue $qsize1 --recvlog
	
    	# humanmotion (== still_on_the_table_with_hands2)
    	echo python runmm.py $chtrace2 -p $port -d ${odir}/_$flowcount --const $npkts 0 --queue $qsize2 --recvlog
    	python runmm.py $chtrace2 -p $port -d ${odir}/_$flowcount --const $npkts 0 --queue $qsize2 --recvlog
	
    	# stationary (== stationary5g)
    	echo python runmm.py $chtrace3 -p $port -d ${odir}/_$flowcount --const $npkts 0 --queue $qsize3 --recvlog
    	python runmm.py $chtrace3 -p $port -d ${odir}/_$flowcount --const $npkts 0 --queue $qsize3 --recvlog
	
    	# walkandturn (== walkandturn5g)
    	echo python runmm.py $chtrace4 -p $port -d ${odir}/_$flowcount --const $npkts 0 --queue $qsize4 --recvlog
    	python runmm.py $chtrace4 -p $port -d ${odir}/_$flowcount --const $npkts 0 --queue $qsize4 --recvlog
    done
done
