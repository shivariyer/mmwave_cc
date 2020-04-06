
#ifndef _CHANNEL_H
#define _CHANNEL_H 

#include <err.h>
#include <time.h>
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
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <iostream>

#define PACKET_SIZE  (size_t) 1024

#define PAYLOAD_LEN  PACKET_SIZE - sizeof(unsigned int) - sizeof(time_t) - sizeof(long) - (size_t) 1

#define LISTENQ      1024

/****************************

// IPv4 socket address structure for reference (from netinet/in.h)
// according to POSIX specification

// structure representing a single IPv4 address
struct in_addr {
  in_addr_t s_addr;  // 32-bit IPv4 address (uint32_t), network-byte
                     // ordered (use ntohx() functions to print
                     // readable output)
};

// structure representing a IPv4 socket address
struct sockaddr_in {
  uint8_t        sin_len;	// length of structure (16 bytes)
  sa_family_t    sin_family;	// AF_INET
  in_port_t      sin_port;	// 16-bit TCP or UDP port number (network-byte ordered)
  struct in_addr sin_addr; 	// 32-bit IPv4 address (network-byte ordered)
  char           sin_zero[8]; 	// unused (for aligning structure to 16 bytes)
};

*****************************/

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
