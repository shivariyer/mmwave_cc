import os
# import arg_parser

time= 60
dir='output'
trace_list = ['humanmotion', 'walkandturn', 'fanrunning', 'stationary', 'Building1_1','Building1_2', 'Building2_1', 'Building2_2', 'Building3_1', 'Building3_2', 'Building4_1', 'Building4_2', 'Building5_1', 'Building5_2', 'InHM_1','InHM_2','InHO_1','InHO_2', 'RMa_1', 'RMa_2', 'UMa_1', 'UMa_2']
    # trace_list = ['humanmotion', 'walkandturn']
bdp_bits_list = [492986.66, 2228554.3, 187462.8, 2408384, 4253769.6, 5234.4504, 5212.0962, 5305.7035, 3989.0823, 4648.8064, 6238.2111, 13326.5972, 4383.2217, 4897.0867, 7792.3615, 7795.7999, 5834.0783, 5987.3378, 106156.6734, 105646845.1, 100631.3198, 105299.4671]
bdp_bytes_list = [61623.3325225, 278569.2875, 23432.85, 301048, 531721.2, 654306.3, 651512.025, 663212.938, 498635.288, 581100.8, 779776.3875, 1665824.65, 547902.7125, 611760.8375, 974045.75, 974474.9875, 729259.7875, 748417.2215, 13269584.175, 13205855.6375, 12578914.975, 13162433.3875] # approximate values of BDP

#buf_len_list = [300000, 500000, 400000, 500000]
buf_len_list_1 = [ 60000, 300000, 25000, 300000, 540000, 655000, 652000, 664000, 499000, 582000, 780000, 1670000, 550000, 612000, 980000, 980000, 730000, 750000, 13300000, 13300000, 12600000, 13200000] # approximations of BDPs
buf_len_list_2 = [120000, 600000, 50000, 600000, 1080000, 1310000, 1304000, 1328000, 998000, 1164000, 1560000, 3340000, 1100000, 124000, 1960000, 1960000, 1460000, 1500000, 26600000, 26600000, 25200000, 26400000] # 2BDP

trace_list = 2 * trace_list
buf_len_list = buf_len_list_1 + buf_len_list_2


for trace, buf_len in zip(trace_list, buf_len_list):
	print('**** Trace: {}, Buffer size: {} bytes ****'.format(trace, buf_len))
	traces=str(trace)
	trace = 'traces/channels/'+str(trace)
	command = "python run.py -tr "+trace
	command += " -t "+str(time)
	command += " -q "+str(buf_len)
	command += " --name "+"{0}_T{1}_128KiB_Q{2}".format(traces,time,buf_len)
	command += " --dir "+dir 
	command += " --algo verus --tcp_probe "
	
	os.system(command)
