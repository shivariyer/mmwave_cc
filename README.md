# mmwave_cc
Testbed for measuring and improving TCP performance over mmWave links

# Requirements
Python 3, NumPy, Pandas, Matplotlib, Make,
[Mahimahi](mahimahi.mit.edu).

# Steps
- Build the client and server programs inside `sender_receiver` by
  typing `make`

- (optional) Test the client and server programs separately by running
  `sender_receiver/sender` and `sender_receiver/receiver` in two
  separate shell instances. The behavior is similar to the iperf
  utility, and the options are a subset of the options available to
  iperf.
  
  - `receiver` needs a port, max number of connections before it
    exits, a verbose option and optional file name for logging the
    output.

  - `sender` needs the server IP address and port. Options are sending
    mode, block size (default: 128 KiB), congestion control algorithm
    to use (default: system default) and optional file name for
    logging. Block size is the amount of data sent in a single
    `send()` call. Sending mode is one of _time to run_ (`-t`) in
    seconds, _number of blocks_ (`-b`) or _trace file_ (`-f`). Trace
    file is expected to contain one number per line showing the
    millisecond. The number of occurrences of a millisecond number
    indicates the number of packets to be sent in that single
    millisecond. The CC algorithm must be one of the available ones in
    `/proc/sys/net/ipv4/tcp_available_congestion_control`.
		
- Run `runmm.py` with mandatory channel trace argument (only the name,
  not the full path). Channel traces are placed in
  `traces/channels`. More channel traces may be added to that
  directory. This program starts a Mahimahi `mm-link` shell to emulate
  the channel, runs the sender and receiver in separate subprocesses,
  saves the output trace and makes a plot of throughput and
  delay. Options to `runmm.py` include those for the sender and
  receiver program and the following: _buffer length_ in bytes for
  Mahimahi (default: infinite), _mm side_ (default: "receiver"),
  whether to use the system iperf utility (`--iperf`) and whether to
  display/save the plots. The _mm side_ argument should be one of
  "sender" or "receiver". If it is "receiver", the receiver program is
  run inside the `mm-link` shell, else the sender is run inside
  `mm-link`. **Note that we have observed problems with running the
  sender inside `mm-link` for TCP flows so we recommend sticking to
  the default "receiver" option for now.** The `--iperf` option is
  currently not implemented.
