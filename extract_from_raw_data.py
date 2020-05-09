import math
import logging
from tqdm import tqdm


class Packet:
    def __init__(self, frame_number, capture_time, sender_ip, recv_ip, seq, ack, next_seq, payload_size):
        self.frame_number = frame_number
        self.capture_time = capture_time
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


def get_pref(preference):
    pref_file = open('tshark_config/preferences')
    pref_list = []
    found_pref = False
    properly_ended = False
    for line in pref_file:

        if not found_pref:
            split_line = line.split(':')[0].strip()
            if split_line == preference:
                found_pref = True
        else:
            stripped_line = line.strip()

            theres_more = False
            if stripped_line[-1] == ',':
                stripped_line = stripped_line[:-1]
                theres_more = True

            pref_list.append(stripped_line)

            if not theres_more:
                properly_ended = True
                break

    if found_pref and properly_ended:
        return pref_list

    print(f"Syntax Error in preferences file! Exiting... found_pref: {found_pref}, properly_ended: {properly_ended}")
    quit()

# The field name has to be the exact name that tshark uses


def get_index(name, some_list):
    try:
        index = some_list.index(name)
    except ValueError:
        print(f"Could not find necessary field {name} in the column entries!")
        print("Make sure to include this field. Exiting...")
        quit()

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
    fields = get_pref("fields")
    frame_index = get_index("frame.number", fields)
    cap_time_index = get_index("frame.time_relative", fields)
    sender_ip_index = get_index("ip.src", fields)
    recv_ip_index = get_index("ip.dst", fields)
    seq_index = get_index("tcp.seq", fields)
    next_seq_index = get_index("tcp.nxtseq", fields)
    ack_index = get_index("tcp.ack", fields)
    load_index = get_index("tcp.len", fields)
    acks_frame_index = get_index("tcp.analysis.acks_frame", fields)
    rtt_index = get_index("tcp.analysis.ack_rtt", fields)

    for line in tshark_file:
        raw_line = line.split()

        packet = Packet(
            frame_number=int(raw_line[frame_index]),
            capture_time=float(raw_line[cap_time_index]),
            sender_ip=raw_line[sender_ip_index],
            recv_ip=raw_line[recv_ip_index],
            seq=int(raw_line[seq_index]),
            next_seq=int(raw_line[next_seq_index]),
            ack=int(raw_line[ack_index]),
            payload_size=int(raw_line[load_index])
        )

        if packet.payload_size == 0:
            # this is an ack packet
            try:
                packet.acks_frame = int(raw_line[acks_frame_index])
                packet.rtt = float(raw_line[rtt_index])
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


# TODO allow user to specify name of file to open and name of file this script produces
def extract():
    logging.basicConfig(filename="extract_errors.log", filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s')

    tshark_file = open("tshark_outfile.txt")

    packet_list = create_packet_list(tshark_file)
    packet_list = get_and_set_rtts(packet_list)

    outfile = open("output/tracename_packet_info.log", 'w')
    outfile.write(
        "my_frame  ts_frame  cap_time  payload  rtt  inter_sent_time\n")

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
                f"{packet.capture_time:.9f}",
                f"{packet.payload_size:04d}",
                f"{packet.rtt:.9f}",
                f"{inter_sent_time:.9f}"
            ]
            info_str = "  ".join(info_list)
            outfile.write(info_str + "\n")
            my_frame += 1


if __name__ == '__main__':
    extract()
