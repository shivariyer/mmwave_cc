
#ifndef _CHANNEL_H
#define _CHANNEL_H 

// general libraries
#include <err.h>
#include <ctime>
#include <csignal>
#include <cstdio>
#include <cstring>
#include <iostream>

// POSIX network libraries
#include <netdb.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>

#define PACKET_SIZE  (size_t) 1472

#define PAYLOAD_LEN  PACKET_SIZE - sizeof(unsigned int) - sizeof(time_t) - sizeof(long)


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
  int seq;			// seq number of packet
  time_t seconds;		// timestamp (seconds)
  long micros;			// timestamp (microseconds)
  char buf[PAYLOAD_LEN];	// payload
} udp_packet_t;

typedef struct __attribute__((packed, aligned(2))) {
  int seq;			// seq number of packet
  size_t bytes;	                // bytes acked (i.e. size of the packet received for which ack was sent)
  time_t seconds;		// timestamp (seconds)
  long micros;			// timestamp (microseconds)
} udp_ack_t;

#endif
