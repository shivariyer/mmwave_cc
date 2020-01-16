
def scale(a):
    return a/1000000.0
    
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



def parse_tcp_delays(filename):
    base_timestamp = 0
    first_timestamp = 0
    last_timestamp = 0
    delays = []
    signal_delay = {}
    pointsx = []
    pointsy = []


    with open(filename) as f:
        for line in f:
            line = line.strip()
            if '# base timestamp' in line:
                base_timestamp = int(line.split(":")[-1])
                continue
            elif line[0] == '#':
                continue

            #print line 
            original = line.split('~')[0]
            words = original.split(' ')
            if len(words) == 4:
                [timestamp, event_type, num_bytes, delay] = words
            elif len(words) == 5:
                [timestamp, event_type, num_bytes, delay, temp] = words
                #print delay
            elif len(words) == 3:
                [timestamp, event_type, num_bytes] = words
                delay = ''

            timestamp = float(timestamp)
            

            #print delay
            timestamp = timestamp - base_timestamp

            if last_timestamp == 0:
                last_timestamp = first_timestamp = timestamp

            last_timestamp = max(timestamp, last_timestamp)

            if event_type == '-':
                if delay == '':
                    print "Delay is not supposed to be nothing for a - event "
                else:
                    delays.append(delay)
        #           signal_delay[timestamp-delay] = min(delay,signal_delay[timestamp-delay])
                    delay = float(delay)
                    pointsx.append(float(timestamp-delay)/1000.0)
                    pointsy.append(delay)

    print len(pointsx), len(pointsy)


    print 'Max delay:', max(pointsy)
    print 'Min delay:', min(pointsy)
    print 'Avg delay:', sum(pointsy) / len(pointsy)
    return pointsy,pointsx


def ms_to_bin(ms,ms_per_bin):
    return int(ms/ms_per_bin)

def bin_to_seconds(b,ms_per_bin):
    return float((b*ms_per_bin)/1000.0)

def parse_tcp_throughput(filename):
    ms_per_bin = 500
    base_timestamp = 0

    f = open(filename)
    input_lines = f.readlines()
    f.close()

    arrivals = {}
    capacities = {}
    departures = {}
    arrival_sum = 0
    capacity_sum = 0
    departure_sum = 0
    bs = []
    min_timestamp = -1
    max_timestamp = -1

    for line in input_lines:
        if '# base timestamp:' in line:
            base_timestamp = float(line.split(':')[-1])
        elif line[0] != '#':
            words = line.split('~')
            temp = words[0].split()
            try:
                timestamp = float(temp[0])
            except ValueError:
                continue
            try:
                event_type = temp[1]
            except IndexError:
                continue

            num_bytes = temp[2]
            delay = 0
            if len(temp) == 4:
                delay = temp[3]

            #to calculate average
            if min_timestamp == -1:
                min_timestamp = timestamp
            if timestamp > max_timestamp:
                max_timestamp = timestamp

            num_bits = int(num_bytes)*8

            b = ms_to_bin(timestamp,ms_per_bin)
            if b not in bs:
                bs.append(b)
            if b not in arrivals:
                arrivals[b] = 0
            if b not in capacities:
                capacities[b] = 0
            if b not in departures:
                departures[b] = 0
            if event_type == '+':
                arrivals[b]+=num_bits
                arrival_sum+=num_bits
            if event_type == '#':
                capacities[b]+=num_bits
                capacity_sum+=num_bits
            if event_type == '-':
                departures[b]+=num_bits
                departure_sum+=num_bits

    #print capacities
    duration = (max_timestamp-min_timestamp)/1000.0
    average_capacity = (capacity_sum/float(duration))/ 1000000.0
    average_ingress = (arrival_sum/float(duration)) / 1000000.0
    average_throughput = (departure_sum/float(duration)) / 1000000.0

    print "average capacity: %f" %average_capacity
    print "average ingress: %f" %average_ingress
    print "average_throughput: %f" %average_throughput

    caps = []
    arr = []
    deps = []
    for b in bs:
        caps.append((capacities[b]/(ms_per_bin/1000.0))/1000000.0)
        arr.append((arrivals[b]/(ms_per_bin/1000.0))/1000000.0)
        deps.append((departures[b]/(ms_per_bin/1000.0))/1000000.0)


    xticks = []
    for b in bs:
        x = bin_to_seconds(b,ms_per_bin)
        if x not in xticks:
            xticks.append(x)
    return xticks,caps,arr,deps