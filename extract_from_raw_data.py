import math
import logging
from tqdm import tqdm

class Packet:
    def __init__(self, frame_number, capture_time, sender_ip, recv_ip, seq, ack, payload_size):
        self.frame_number = frame_number
        self.capture_time = capture_time
        self.sender_ip = sender_ip #not currently used
        self.recv_ip = recv_ip #not currently used
        self.seq = seq
        self.ack = ack
        self.payload_size = payload_size
        self.acked_time = math.inf
        self.prev_packet_capture_time = math.inf
        #self.was_retransmitted = False

    # the inter arrival time of packets with payload
    def get_iat_recv(self):
        return self.capture_time - self.prev_packet_capture_time

    # delay from sender to receiver
    #currently just the same as delay2 but this has to change
    def get_delay1(self):
        return self.acked_time - self.capture_time 

    # delay from receiver to sender
    def get_delay2(self):
        return self.acked_time - self.capture_time

    def get_rtt(self):
        return self.get_delay1() + self.get_delay2()

def find_match(substring, line):
    for string in line:
        ss_len = len(substring)
        if substring == string[:ss_len]:
            return string
    return ""

def create_packet_list(tshark_file):
    all_packets = []
    for line in tshark_file:
        raw_line = line.split()

        seq = find_match('Seq=', raw_line).split('=')[1]
        ack = find_match('Ack=', raw_line).split('=')[1]
        payload_size = find_match('Len=', raw_line).split('=')[1]

        packet = Packet(
            frame_number=int(raw_line[0]),
            capture_time=float(raw_line[1]),
            sender_ip=raw_line[2],
            recv_ip=raw_line[4],
            seq=int(seq),
            ack=int(ack),
            payload_size=int(payload_size)
        )

        all_packets.append(packet)

    return all_packets

def find_acked_segment(ack_packet, packet_list):
    #for range from ack_packet.frame to 0. If time < (ack_packet.capture_time - .3) break
    for curr_frame in range(ack_packet.frame_number-1, -1, -1):
        curr_packet = packet_list[curr_frame]

        #arbitrarily setting 'timeout' to 1 second (could probably make this shorter)
        if curr_packet.capture_time < (ack_packet.capture_time - 1):
            break

        #explain line
        if curr_packet.seq == (ack_packet.ack - curr_packet.payload_size):
            return curr_packet
   
    logging.warning(
        f"Could not find segement associated with this ACK! ACK frame: {ack_packet.frame_number}, ACK's ack: {ack_packet.ack}, Wanted to find: {ack_packet.ack - 1448}")
    return None

def find_prev_packet_in_sequence(payload_packet, packet_list):
    for curr_frame in range(payload_packet.frame_number-1, -1, -1):
        curr_packet = packet_list[curr_frame]

        #explain line
        if curr_packet.seq == (payload_packet.seq - curr_packet.payload_size):
            return curr_packet
    
    logging.warning(f"Could not find previous segement! Payload frame: {payload_packet.frame_number}, Packet Seq: {payload_packet.seq}, Wanted to find: {payload_packet.seq - curr_packet.payload_size}")
    return None


#TODO allow user to specify name of file to open and name of file this script produces
if __name__ == '__main__':
    logging.basicConfig(filename="extract_errors.log", filemode='w', format='%(name)s - %(levelname)s - %(message)s')

    tshark_file = open("raw_packet_data.txt")

    packet_list = create_packet_list(tshark_file)

    print("Matching up packets...")
    for i in tqdm(range(len(packet_list)), ncols=80):
        packet = packet_list[i]

        if packet.payload_size == 0: #This is an ACK and was sent to the sender

            acked_packet = find_acked_segment(packet, packet_list)
            if acked_packet == None:
                continue

            if acked_packet.acked_time < math.inf:
                logging.warning(f"Packet {acked_packet.frame_number} produced multiple ACKs! What do? ACK match: {acked_packet.seq + acked_packet.payload_size}")
            else:
                acked_packet.acked_time = packet.capture_time

        else: #This packet contains a payload and was sent to the receiver
            if packet.frame_number == 1:
                continue #SET THIS PROPERLY
            prev_packet = find_prev_packet_in_sequence(packet, packet_list)
            if prev_packet == None:
                continue
            packet.prev_packet_capture_time = prev_packet.capture_time

    #maybe need to fetch the start and end flow times from sender and recv logs

    outfile = open("tracename_packet_info.log", 'w')
    outfile.write("my_frame  ts_frame  cap_time  payload  iat  delay1  delay2  rtt\n")

    my_frame = 1
    for packet in packet_list:
        if packet.payload_size > 0:
            info_list = [
                f"{my_frame:06d}",
                f"{packet.frame_number:06d}",
                f"{packet.capture_time:.9f}",
                f"{packet.payload_size:04d}",
                f"{packet.get_iat_recv():.9f}",
                f"{packet.get_delay1():.9f}",
                f"{packet.get_delay2():.9f}",
                f"{packet.get_rtt():.9f}"
            ]
            info_str = "  ".join(info_list)
            outfile.write(info_str + "\n")
            my_frame += 1


    # test_list = []
    # for packet in packet_list:
    #     if packet.seq > 1:
    #         test_list.append(packet.seq)
    
    # test_list.sort()
    # prev = -1
    # for seq in test_list:
    #     if seq == prev:
    #         print(seq)
    #     prev = seq