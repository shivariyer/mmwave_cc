#!/bin/bash

# run emulation on mahimahi for list of user sender traces

# tr=fan_running5
odir=output #/$1
adir=analysis
fdir=figures
ddir=dataset
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

cong_algo=reno

let maxflows=1

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
    	echo python3 runmm.py $chtrace1 -d ${odir} -q $qsize1 --cc-algo $cong_algo --ttr 2 -v -v
    	python3 runmm.py $chtrace1 -d ${odir} -q $qsize1 --cc-algo $cong_algo --ttr 2 -v -v
		#python3 ${chtrace1}_const_${npkts}_${probe}_q${qsize1} -if $odir -of $adir -ff $fdir
	
    	# # humanmotion (== still_on_the_table_with_hands2)
    	# echo python3 runmm.py $chtrace2 -d ${odir} -q $qsize2 --cc-algo $cong_algo
    	# python3 runmm.py $chtrace2 -d ${odir} -q $qsize2 --cc-algo $cong_algo
	
    	# # stationary (== stationary5g)
    	# echo python3 runmm.py $chtrace3 -d ${odir} -q $qsize3 --cc-algo $cong_algo
    	# python3 runmm.py $chtrace3 -d ${odir} -q $qsize3 --cc-algo $cong_algo
	
    	# # walkandturn (== walkandturn5g)
    	# echo python3 runmm.py $chtrace4 -d ${odir} -q $qsize4 --cc-algo $cong_algo
    	# python3 runmm.py $chtrace4 -d ${odir} -q $qsize4 --cc-algo $cong_algo
	
    done
done
