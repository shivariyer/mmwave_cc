#!/bin/bash

# run emulation on mahimahi for list of user sender traces

odir=output
adir=analysis
fdir=figures
ddir=dataset
seed=0
port=9999

traces=("fanrunning" "humanmotion" "stationary" "walkandturn")
#qsizes=(400000 300000 500000 500000)
qsizes=(200000 150000 250000 250000)


#get length of traces array
t_len=${#traces[@]}

cong_algo=reno

block_size=4096

ttr_flag="-t 10"
ttr=T10
nblocks_flag="-n 11"
nblocks=N11
method_with_flag=$ttr_flag
method=$ttr
link_type=downlink

hist=20
#RUNMM
for ((i=0; i<${t_len}; i++));
do
    # #RUNMM
    # echo python3 runmm.py ${traces[$i]} -d ${odir} -q ${qsizes[$i]}  -b $block_size --cc-algo $cong_algo $method_with_flag --save-plot -v -v
    # python3 runmm.py ${traces[$i]} -d ${odir} -q ${qsizes[$i]} -b $block_size --cc-algo $cong_algo $method_with_flag --save-plot -v -v

    # #CREATE CSVS
    # echo python3 create_csvs_and_plot.py ${traces[$i]}_${method}_${block_size}KiB_Q${qsizes[$i]} -d $link_type -if $odir -of $adir -ff $fdir
    # echo This is gonna take a while. Go watch Netflix...
    # python3 create_csvs_and_plot.py ${traces[$i]}_${method}_${block_size}KiB_Q${qsizes[$i]} -d $link_type -if $odir -of $adir -ff $fdir

    #MAKE DATASET
    python3 make_dataset.py \
        --filespec ${traces[$i]}_${method}_${block_size}KiB_Q${qsizes[$i]}_${link_type} \
        --history $hist \
        --outnamesuffix ${traces[$i]}_${qsizes[$i]}_make_dataset_out -if $adir -of $ddir --yes

done