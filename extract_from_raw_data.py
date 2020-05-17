import math
import logging
import os
import sys
from tqdm import tqdm


class Packet:
    def __init__(self, frame_number, capture_time, epoch_time, sender_ip, recv_ip, seq, ack, next_seq, payload_size):
        self.frame_number = frame_number
        self.capture_time = capture_time
        self.epoch_time = epoch_time
        self.sender_ip = sender_ip  # not currently used
        self.recv_ip = recv_ip  # not currently used
        self.seq = seq
        self.ack = ack
        self.next_seq = next_seq
        self.payload_size = payload_size
        # these two values will get set if this is an ack packet
        self.acks_frame = math.inf
        self.rtt = math.inf

    # the inter arrival time of packets with payload
    def get_iat_recv(self):
        return self.capture_time - self.prev_packet_capture_time

    # delay from sender to receiver
    # currently just the same as delay2 but this has to change
    def get_delay1(self):
        return self.acked_time - self.capture_time

    # delay from receiver to sender
    def get_delay2(self):
        return self.acked_time - self.capture_time

    def get_rtt(self):
        return self.get_delay1() + self.get_delay2()


def get_fields(tshark_file):
    for line in tshark_file:
        if line[-1] == '\n':
            line = line[:-1]
        fields_list = line.split(',')
        break
    return fields_list


def get_index(name, some_list):
    try:
        index = some_list.index(name)
    except ValueError:
        print(f"Could not find necessary field {name} in the column entries!")
        print("Make sure to include this field. Exiting...")
        sys.exit(-1)

    return index


def find_match(substring, line):
    for string in line:
        ss_len = len(substring)
        if substring == string[:ss_len]:
            return string
    return ""


def create_packet_list(tshark_file):
    all_packets = []

    # Get indexes of required fields
    fields = get_fields(tshark_file)
    
    frame_index = get_index("frame.number", fields)
    cap_time_index = get_index("frame.time_relative", fields)
    epoch_time_index = get_index("frame.time_epoch", fields)
    sender_ip_index = get_index("ip.src", fields)
    recv_ip_index = get_index("ip.dst", fields)
    seq_index = get_index("tcp.seq", fields)
    next_seq_index = get_index("tcp.nxtseq", fields)
    ack_index = get_index("tcp.ack", fields)
    load_index = get_index("tcp.len", fields)
    acks_frame_index = get_index("tcp.analysis.acks_frame", fields)
    rtt_index = get_index("tcp.analysis.ack_rtt", fields)

    # Note: the first line was already skipped in get_fields()
    for line in tshark_file:
        if line[-1] == '\n':
            line = line[:-1]
        packet_data = line.split()

        packet = Packet(
            frame_number=int(packet_data[frame_index]),
            capture_time=float(packet_data[cap_time_index]),
            epoch_time=float(packet_data[epoch_time_index]),
            sender_ip=packet_data[sender_ip_index],
            recv_ip=packet_data[recv_ip_index],
            seq=int(packet_data[seq_index]),
            next_seq=int(packet_data[next_seq_index]),
            ack=int(packet_data[ack_index]),
            payload_size=int(packet_data[load_index])
        )

        if packet.payload_size == 0:
            # this is an ack packet
            try:
                packet.acks_frame = int(packet_data[acks_frame_index])
                packet.rtt = float(packet_data[rtt_index])
            except IndexError:
                logging.warning(f"possible ack packet {packet.frame_number} does not contain acks_frame and rtt")

        all_packets.append(packet)

    return all_packets


def get_and_set_rtts(packet_list):
    for packet in packet_list:
        if packet.payload_size == 0:
            try:
                packet_list[packet.acks_frame-1].rtt = packet.rtt
            except TypeError:
                logging.warning(f'packet ts_frame number: {packet.frame_number} was declared as ack but has no acks_frame')
    return packet_list

#a hard coded fix
def add_fields_to_file(filename):
    fp = open(filename, 'w')
    fields = [
        "frame.number",
        "frame.time_epoch",
        "frame.time_relative",
        "ip.src",
        "ip.dst",
        "_ws.col.Protocol",
        "tcp.seq",
        "tcp.nxtseq",
        "tcp.ack",
        "tcp.len",
        "tcp.analysis.acks_frame",
        "tcp.analysis.ack_rtt"
    ]
    result = ""
    for field in fields:
        result += field + ','
    fp.write(result + '\n')
    fp.close()

def get_nth_occurrence(some_str, substr, n):
    parts = some_str.split(substr, n+1)
    if len(parts) <= n + 1:
        return -1
    return len(some_str) - len(parts[-1]) - len(substr)


# TODO allow user to specify name of file to open and name of file this script produces
def extract(ifolder, trace):
    logging.basicConfig(filename="extract_errors.log", filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s')


    where_to_chop = get_nth_occurrence(trace, "_", 1)
    trace = trace[:where_to_chop]

    # first convert pcapng file to text
    add_fields_to_file(f"{ifolder}/{trace}_packet_data.txt")
    os.system(f"tshark -r {ifolder}/{trace}_capture >> {ifolder}/{trace}_packet_data.txt")

    tshark_file = open(f"{ifolder}/{trace}_packet_data.txt")
    packet_list = create_packet_list(tshark_file)
    tshark_file.close()

    packet_list = get_and_set_rtts(packet_list)

    outfile = open(f"{ifolder}/{trace}_packet_info.log", 'w')
    outfile.write(
        "my_frame  ts_frame  epoch_time  cap_time  payload  rtt  inter_sent_time\n")

    # adding my own frame numbers for the payload packets
    # and recording the time between two packets being sent
    my_frame = 1
    prev_sent_time = 0.0
    for packet in packet_list:
        if packet.payload_size > 0:
            # have to record the prev_sent_time before
            # checking if this packet will be used in our data
            # because even if we dont use some payload packet
            # it was still sent so we record the sent time
            inter_sent_time = packet.capture_time - prev_sent_time
            prev_sent_time = packet.capture_time
            # We will only use the packets that have an rtt associated with them
            if not packet.rtt < math.inf:
                continue
            info_list = [
                f"{my_frame:06d}",
                f"{packet.frame_number:06d}",
                f"{packet.epoch_time:.9f}",
                f"{packet.capture_time:.9f}",
                f"{packet.payload_size:04d}",
                f"{packet.rtt:.9f}",
                f"{inter_sent_time:.9f}"
            ]
            info_str = "  ".join(info_list)
            outfile.write(info_str + "\n")
            my_frame += 1

    outfile.close()


if __name__ == '__main__':
    extract()
