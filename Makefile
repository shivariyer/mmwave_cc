path = ./sender_receiver/
execs = $(path)sender $(path)receiver

all: $(execs)

sender: $(path)sender.cc
receiver: $(path)receiver.cc

.PHONY: clean
clean:
	rm -f $(execs)