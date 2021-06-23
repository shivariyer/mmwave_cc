execs = udp_sender udp_receiver

all: $(execs)

udp_sender: udp_sender.cc
	g++ -pthread -g -o udp_sender udp_sender.cc
udp_receiver: udp_receiver.cc

.PHONY: clean
clean:
	rm -f $(execs)
