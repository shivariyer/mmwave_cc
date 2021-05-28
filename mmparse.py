import os

# parsing a trace file
def parse_trace_file(filename, pkt_size=1492):
    f1 = open (filename,"r")
    BW = []
    nextTime = 1000
    cnt = 0
    for line in f1:
        #print line
        if int(line.strip()) > nextTime:
            BW.append(cnt*pkt_size*8)
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


def parse_mm_throughput(filepath, ms_per_bin=1000, verbose=True):
    
    from tqdm import tqdm
    from numpy import asarray
    from pandas import DataFrame, Index
    
    # data contains (ms, cap, arr, dep)
    init_timestamp = None
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
            if line.startswith('# init timestamp'):
                init_timestamp = int(line.split(':')[-1]) 
            elif line.startswith('# base timestamp'):
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
    
    result_dict = {'init_timestamp' : round(init_timestamp / 1000),
                   'duration_ms' : ms_elapsed,
                   'capacity_avg' : cap_avg_Mbps,
                   'ingress_avg' : ingress_avg_Mbps,
                   'throughput_avg' : tput_avg_Mbps,
                   'capacity' : data.capacity,
                   'ingress' : data.ingress,
                   'throughput' : data.throughput,
                   'utilization' : (tput_avg_Mbps / cap_avg_Mbps) * 100}
                   
    return result_dict


def parse_mm_log_simple(mmfilepath):
    # for every millisecond, log the ingress, egress, dropped,
    # capacity queue size and the queue occupancy
    mm_times = []
    mm_ingress = []
    mm_egress = []
    mm_dropped = []
    mm_qsize = []
    mm_capacity = []

    # constants
    mm_init_timestamp = 0
    q_type = None
    qsize_unit = None
    qsize_limit = None

    # computed every millisecond ('ms')
    tick_ms_last = 0
    ingress_ms_last = 0
    egress_ms_last = 0
    dropped_ms_last = 0
    qsize_ms_last = 0
    cap_ms_last = 0

    # last op
    op_last = None
    bytes_last = None
    
    with open(mmfilepath) as fin:
        
        t = tqdm(total=os.stat(mmfilepath).st_size, desc='Parsing the mm log')
        
        for line in fin:
            
            # ignore commented lines except the ones containing init
            # time and the queue information
            if line.startswith('#'):
                if 'init timestamp:' in line:
                    mm_init_timestamp = int(line.split(':')[1])
                elif 'queue:' in line:
                    match = re.match('# queue: (\w+)\s*(\[(\w+)=(\d+)\])?', line).groups()
                    q_type, qsize_unit = match[0], match[2]
                    if q_type != 'infinite':
                        qsize_limit = int(match[3])
                continue

            # parse the line
            words = line.strip().split()
            op = words[1]
            tick_ms = int(words[0])
            qsize_ms = int(words[-1])

            # new millisecond tick
            if tick_ms > tick_ms_last and tick_ms_last != 0:
                mm_times.append(tick_ms_last)
                mm_ingress.append(ingress_ms_last)
                mm_egress.append(egress_ms_last)
                mm_dropped.append(dropped_ms_last)
                if op_last == '+':
                    # if the last operation is an addition, then
                    # the queue size isn't updated on the same
                    # line, so update it now
                    qsize_ms_last += bytes_last
                mm_qsize.append(qsize_ms_last)
                mm_capacity.append(cap_ms_last)
                ingress_ms_last = 0
                egress_ms_last = 0
                dropped_ms_last = 0
                cap_ms_last = 0

                # if some milliseconds were skipped, then fill in for
                # those also
                tick_ms_last += 1
                while tick_ms > tick_ms_last:
                    mm_times.append(tick_ms_last)
                    mm_qsize.append(qsize_ms_last)
                    mm_ingress.append(0)
                    mm_egress.append(0)
                    mm_dropped.append(0)
                    mm_capacity.append(0)
                    tick_ms_last += 1
            
            tick_ms_last = tick_ms
            qsize_ms_last = qsize_ms
            
            # '#' indicates departure opportunity (i.e. capacity in
            # the network)
            if op == '#':
                bytes_last = int(words[2].split('~')[0])
                cap_ms_last += bytes_last

            # '+' indicates ingress (i.e. a new packet arriving)
            elif op == '+':
                bytes_last = int(words[2].split('~')[0])
                ingress_ms_last += bytes_last

            # '-' indicates egress (i.e. a packet leaving the queue)
            elif op == '-':
                bytes_last = int(words[2])
                egress_ms_last += bytes_last

            # 'd' indicates packet dropped
            elif op == 'd':
                bytes_last = int(words[3].split('~')[0])
                dropped_ms_last += bytes_last

            op_last = op

            t.update(len(line))
        
        # end of for loop
        t.close()
        
    # aggregate everything computed in the final millisecond
    mm_times.append(tick_ms_last)
    mm_ingress.append(ingress_ms_last)
    mm_egress.append(egress_ms_last)
    mm_dropped.append(dropped_ms_last)
    if op_last == '+':
        qsize_ms_last += bytes_last
    mm_qsize.append(qsize_ms_last)
    mm_capacity.append(cap_ms_last)

    res = np.vstack((mm_times, mm_ingress, mm_egress, mm_dropped, mm_capacity, mm_qsize)).astype(np.float).T

    # add init timestamp to offset the ms ticks and make the unit
    # "seconds"
    res[:,0] = (res[:,0] + mm_init_timestamp) / 1000.0

    # write parsed output into file
    with open(mmfilepath[:-4] + '_parsed.txt', 'w') as fout:
        hdr_fmt = '{:>17s},{:>14s},{:>13s},{:>14s},{:>15s},{:>11s},{:>16s}' + os.linesep
        row_fmt = '{:17.6f},{:>14.0f},{:>13.0f},{:>14.0f},{:15.0f},{:11.0f},{:16.5f}' + os.linesep

        fout.write('# queue: {}, length: {} {}'.format(q_type, qsize_limit, qsize_unit) + os.linesep)
        fout.write(hdr_fmt.format('unix_time', 'ingress_bytes', 'egress_bytes', 'dropped_bytes',  'capacity_bytes', 'queue_size', 'queue_occupancy'))
        for row in tqdm(res, desc='Printing out the table'):
            fout.write(row_fmt.format(row[0], row[1], row[2], row[3], row[4], row[5], row[5]/qsize_limit))

    return res, (q_type, qsize_unit, qsize_limit)


if __name__ == '__main__':
    # cmdline arg is mmlink downlink log file
    logfilepath = sys.argv[1]

    res, q_info = parse_mm_log_simple(logfilepath)
    print(q_info)
