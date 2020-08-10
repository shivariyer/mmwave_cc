import os
# import arg_parser

time= 60
dir='output'
trace_list = ['humanmotion', 'walkandturn', 'fanrunning', 'stationary', 'Building1_1','Building1_2', 'Building2_1', 'Building2_2', 'Building3_1', 'Building3_2', 'Building4_1', 'Building4_2', 'Building5_1', 'Building5_2', 'InHM_1','InHM_2','InHO_1','InHO_2', 'RMa_1', 'RMa_2', 'UMa_1', 'UMa_2']
    



bdp_bits_list = [123.108 ,207.376, 165.170, 204.201, 1029.587, 1025.267, 1026.114, 1013.581, 1046.954, 1059.427, 996.179, 990.055, 1034.159, 1033.335, 1028.274, 1033.634, 1021.889, 1028.072, 102.506, 102.315, 115.863, 103.139]
bdp_bytes_list = [15388.5, 25922, 20646.25, 25525.125, 128698.375, 128158.375, 128264.25, 126697.625, 130869.25, 132428.375, 124522.375, 123756.875, 129269.875, 129166.875, 128534.25, 129204.25, 127736.125, 128509, 12813.25, 12789.375, 14482.875, 12892.375]
buf_len_list_1 = [15400  , 26000, 21000   , 26000    , 130000    , 130000    , 130000   , 130000    , 131000   , 133000    , 125000    , 124000    , 130000    , 130000    , 129000   , 130000   , 130000    , 130000, 13000   , 13000    , 15000    , 13000]
buf_len_list_2 = [30800  , 52000, 42000   , 52000    , 260000    , 260000    , 260000   , 260000    , 262000   , 266000    , 250000    , 248000    , 260000    , 260000    , 258000   , 260000   , 260000    , 260000, 26000   , 26000    , 30000    , 26000]

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
	command += " --algo copa"
	
	os.system(command)
