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
                words = line.split()
                if words[1] == '-':
                    timestamp = int(words[0]) - base_timestamp
                    #double check that this is the correct split and word
                    delay = float(words[3].split('~')[0])
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
                words = line.split()
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
                pkt_len_bits = int(words[2].split('~')[0]) * 8
                
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


def parse_mm_log(mmfilepath, debug=False):
    
    import os
    import re
    from tqdm import tqdm
    from numpy import inf, vstack
    
    mmtimes = []
    mmadditions = []
    mmsubtractions = []
    capacity = []
    mmqsize = []
    
    if debug:
        print('Copying input to output augmented with queue size for debugging...')
        lines_aug = []
    
    mm_init_timestamp = 0

    queue_info = None
    
    with open(mmfilepath) as fin:
        
        # The queue length computed by the modified version of
        # mahimahi by Talal is inconsistent. During queue additions,
        # the queue length is updated in the next entry, whereas for
        # removals, it is updated on the same line. It finally
        # reflects the correct queue length at the end, when the queue
        # is correctly empty, but when switching from removal ('-') to
        # addition ('+'), without an opportunity ('#') in between, the
        # value is one lower than the correct value (see millisecond
        # 7940 in *_INCONSISTENCY.csv). Still, we need to use it
        # because it eventually shows the correct no of packets in the
        # queue, and our queue length computation must use it to be
        # consistent.
        
        queue_len_last = 0
        #queue_len_mmadd_last = 0
        #pkt_len_bytes_last = 0
        
        # computed every millisecond ('ms')
        tick_ms_last = 0
        mmadditions_ms_last = 0
        mmsubtractions_ms_last = 0
        queue_len_bytes_cur = 0
        cap_ms_last = 0
        
        # flag
        queue_is_full = False
        
        queue_len_max = inf
        QUEUE_LEN_BYTES_MAX = inf
        
        t = tqdm(total=os.stat(mmfilepath).st_size, desc='Parsing the mm log')
        
        for line in fin:
            
            # ignore commented lines except one containing init time
            if line.startswith('#'):
                if debug:
                    lines_aug.append(line)
                if 'init timestamp:' in line:
                    mm_init_timestamp = int(line.split(':')[1])
                elif 'queue:' in line:
                    # TODO: handle other types of queues here and
                    # units other than bytes
                    match = re.match('# queue: (\w+)\s*(\[(\w+)=(\d+)\])?', line)
                    groups = match.groups()
                    print(groups)
                    QUEUE_TYPE, QUEUE_LEN_UNIT = groups[0], groups[2]
                    if QUEUE_TYPE != 'infinite':
                        assert QUEUE_LEN_UNIT == 'bytes'
                        QUEUE_LEN_BYTES_MAX = int(groups[3])
                        queue_info = (QUEUE_TYPE, QUEUE_LEN_BYTES_MAX)
                continue
            
            words = line.strip().split()
            tick_ms = int(words[0])
            
            # new millisecond tick
            if tick_ms_last != tick_ms:
                
                mmtimes.append(tick_ms)
                
                # aggregate everything computed in the last
                # millisecond, except in the very first millisecond
                if tick_ms_last != 0:
                    mmadditions.append(mmadditions_ms_last)
                    mmadditions_ms_last = 0
                    
                    mmsubtractions.append(mmsubtractions_ms_last)
                    mmsubtractions_ms_last = 0
                    
                    mmqsize.append(queue_len_bytes_cur)
                    
                    capacity.append(cap_ms_last)
                    cap_ms_last = 0
                
                tick_ms_last = tick_ms
            
            # '#' indicates departure opportunity (i.e. capacity in
            # the network)
            if words[1] == '#':
                pkt_len_bytes, queue_len = map(int, words[2].split('~'))
                cap_ms_last += pkt_len_bytes
            
            # '+' indicates additional packet added to the
            # mahimahi queue so that the queue size increases
            elif words[1] == '+':                
                pkt_len_bytes, queue_len = map(int, words[2].split('~'))
                
                # # a packet arrives at the queue, and is not dropped,
                # # so count it in queue length
                # if queue_len > 0 and queue_len_mmadd_last == queue_len:
                #     # queue is full
                #     if not queue_is_full:
                #         # this is because queue_len is recorded
                #         # post-facto (in the next line), the last pkt
                #         # counted in queue_len_bytes_cur must be
                #         # excluded
                #         if mmadditions_ms_last > 0:
                #             queue_len_bytes_cur -= pkt_len_bytes_last
                #             mmadditions_ms_last -= 1
                #         else:
                #             mmqsize[-1] -= pkt_len_bytes_last
                #             mmadditions[-1] -= 1
                #         queue_is_full = True
                # else:
                #     queue_len_bytes_cur += pkt_len_bytes
                #     mmadditions_ms_last += 1
                #     #queue_len_mmadd_last = queue_len
                
                if not queue_is_full:
                    queue_len_bytes_new = queue_len_bytes_cur + pkt_len_bytes
                    if queue_len_bytes_new <= QUEUE_LEN_BYTES_MAX:
                        # buffer has space for the packet
                        queue_len_bytes_cur = queue_len_bytes_new
                        mmadditions_ms_last += 1
                    else:
                        queue_is_full = True
                        queue_len_max = queue_len
            
            # '-' indicates packet removal from the mahimahi queue
            # so that the queue size is reduced
            elif words[1] == '-':
                pkt_len_bytes = int(words[2])
                queue_len = int(words[3].split('~')[1])
                
                # to handle a special case of inconsistency that's
                # hard to fix without editing the logging code in
                # mahimahi itself
                if queue_len < queue_len_last or queue_len < queue_len_max:
                    # first cond MUST be true before any decrement
                    # happens, because for removals, the updated no of
                    # packets in queue is printed on the same
                    # line. But in practice, it fails when queue is
                    # full, hence the second cond.
                    queue_len_bytes_cur -= pkt_len_bytes
                    mmsubtractions_ms_last += 1
                
                if queue_is_full:
                    queue_is_full = False
            
            # loop updates
            #if queue_is_full and queue_len < queue_len_mmadd_last:
            #     queue_is_full = False
            
            if debug:
                if queue_is_full:
                    lines_aug.append(line.strip() + ' {}!'.format(queue_len_bytes_cur) + os.linesep)
                else:
                    lines_aug.append(line.strip() + ' {}'.format(queue_len_bytes_cur) + os.linesep)
            
            queue_len_last = queue_len
            #pkt_len_bytes_last = pkt_len_bytes
            
            t.update(len(line))
        
        # end of for loop
        
        t.close()
        
        # aggregate everything computed in the final millisecond
        mmadditions.append(mmadditions_ms_last)
        mmsubtractions.append(mmsubtractions_ms_last)
        mmqsize.append(queue_len_bytes_cur)
        capacity.append(cap_ms_last)
        
        res = vstack((mmtimes, mmadditions, mmsubtractions, mmqsize, capacity)).T
        res[:,0] += mm_init_timestamp # add init timestamp to first column (mmtimes)
        
        if debug:
            # copy input dump into output dump, but augmented with queue
            # length (in bytes) at every time instant (to help track queue
            # size manually at a later point)
            mmfilename = os.path.basename(mmfilepath)
            with open(mmfilename[:-4] + '_qlenbytes.csv', 'w') as fout:
                fout.writelines(lines_aug)
        
        return mm_init_timestamp, res, queue_info