import os

# parsing a trace file
def parse_trace_file(filename):
    f1 = open (filename,"r")
    BW = []
    nextTime = 1000
    cnt = 0
    for line in f1:
        #print line
        if int(line.strip()) > nextTime:
            BW.append(cnt*1492*8)
            cnt = 0
            nextTime+=1000
        else:
            cnt+=1
    f1.close()
    return BW


def parse_mm_queue_delays(filepath):
    base_timestamp = 0
    delays = []
    delaytimes = []
    
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line.startswith('# base timestamp'):
                base_timestamp = int(line.split(":")[-1])
                continue
            elif not line.startswith('#'):
                words = line.split('~')[0].split()
                if words[1] == '-':
                    timestamp = int(words[0]) - base_timestamp
                    delay = float(words[3])
                    delays.append(delay)
                    delaytimes.append(float(timestamp - delay) / 1000.0)
    
    return delays, delaytimes


def parse_mm_throughput(filepath, ms_per_bin=500, verbose=True):
    
    from tqdm import tqdm
    from numpy import asarray
    from pandas import DataFrame, Index
    
    # data contains (ms, cap, arr, dep)
    base_timestamp = 0
    
    ms_index = [0]
    data = [[0, 0, 0]]
    
    cap_total = 0
    dep_total = 0
    arr_total = 0
    
    bin_cur = 0
    
    with open(filepath) as f:

        if (verbose):
            t = tqdm(total=os.stat(filepath).st_size, desc='Parsing mm log')
        
        for line in f:
            if line.startswith('# base timestamp'):
                base_timestamp = int(line.split(":")[-1])
                continue
            elif not line.startswith('#'):
                words = line.split('~')[0].split()
                ms_elapsed = int(words[0]) - base_timestamp
                bin_i = ms_elapsed // ms_per_bin
                if bin_i > bin_cur:
                    # new bin
                    for i in range(bin_cur+1, bin_i+1):
                        # if we jumped some bins, then fill those with
                        # zeros
                        ms_index.append(i)
                        data.append([0, 0, 0])
                    bin_cur = bin_i
                
                event_type = words[1]
                pkt_len_bits = int(words[2]) * 8
                
                if event_type == '#':
                    data[-1][0] += pkt_len_bits
                    cap_total += pkt_len_bits
                elif event_type == '+':
                    data[-1][1] += pkt_len_bits
                    arr_total += pkt_len_bits
                elif event_type == '-':
                    data[-1][2] += pkt_len_bits
                    dep_total += pkt_len_bits

            if verbose:
                t.update(len(line))

        if verbose:
            t.close()
    
    # end of loop
    
    # compute avg cap, ingress and tput
    cap_avg_Mbps = (cap_total / ms_elapsed) / 1000.0
    ingress_avg_Mbps = (arr_total / ms_elapsed) / 1000.0
    tput_avg_Mbps = (dep_total / ms_elapsed) / 1000.0
    
    # print('Avg cap (Mbps):', cap_avg_Mbps)
    # print('Ingress rate (Mbps):', ingress_avg_Mbps)
    # print('Throughput (Mbps):', tput_avg_Mbps)
    
    # compute cap, ingress and tput per bin and put it in a table
    data = DataFrame(asarray(data) / (ms_per_bin * 1000.0),
                     Index(ms_index, name='seconds') * ms_per_bin / 1000,
                     columns=['capacity', 'ingress', 'throughput'])
    
    result_dict = {'duration_ms' : ms_elapsed,
                   'capacity_avg' : cap_avg_Mbps,
                   'ingress_avg' : ingress_avg_Mbps,
                   'throughput_avg' : tput_avg_Mbps,
                   'capacity' : data.capacity,
                   'ingress' : data.ingress,
                   'throughput' : data.throughput,
                   'utilization' : (tput_avg_Mbps / cap_avg_Mbps) * 100}
                   
    return result_dict
