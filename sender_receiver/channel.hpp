
#ifndef _CHANNEL_H
#define _CHANNEL_H 

#include <err.h>
#include <errno.h>
#include <netdb.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <iostream>

#define MTU 1500
#define PAYLOAD_LEN 1483

typedef struct __attribute__((packed, aligned(2))) {
  unsigned int seq;		// seq number of packet
  time_t seconds;		// timestamp (seconds)
  long micros;			// timestamp (microseconds)
  bool probe;			// whether this a probe packet or bg traffic packet
  char buf[PAYLOAD_LEN];	// payload
} packet_t;

typedef struct __attribute__((packed, aligned(2))) {
  unsigned int seq;		// seq number of packet
  time_t seconds;		// timestamp (seconds)
  long micros;			// timestamp (microseconds)
  bool probe;	                // whether this a probe packet or bg traffic packet
  double iat;	                // time elapsed between last two packets ("iat")
} ack_t;

#endif
