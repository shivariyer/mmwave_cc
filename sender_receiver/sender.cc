#include "channel.hpp"

using namespace std;


extern int errno;
//int err;
static FILE *logfp;
struct timeval timestamp;

/* send_const: send a lumpsum of number of packets in a single tcp flow. */
int
send_const(char *serv_ip, int serv_port, char *cc_protocol, int num_packets, bool probe) {

  // establish connection first
  struct sockaddr_in serv_addr;

  int sockfd;
  
  // opening a tcp socket
  if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) == -1)
    err(-1, "socket");

  int enabled = 1;
  if ((setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &enabled, sizeof(enabled)) != 0))
    err(-1, "sockopt SO_REUSEADDR");
  
  if ((setsockopt(sockfd, IPPROTO_TCP, TCP_CONGESTION, cc_protocol, strlen(cc_protocol)) != 0))
    err(-1, "sockopt TCP_CONGESTION");
  
  // connect to the server
  memset(&serv_addr, 0, sizeof(serv_addr));
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(serv_port);
  //serv_addr.sin_addr.s_addr = inet_addr(serv_ip);
  if (inet_pton(AF_INET, serv_ip, &serv_addr.sin_addr) <= 0)
    err(-1, "inet_pton");
  
  if (connect(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
    err(-1, "connect");
  
  // report successful connection to server
  
  // print server address and port
  char serv_addr_p[INET_ADDRSTRLEN] = "X.X.X.X";
  if (inet_ntop(AF_INET, &serv_addr.sin_addr, serv_addr_p, INET_ADDRSTRLEN) == NULL) 
    warn("inet_ntop");
  
  // print host name and service (DNS lookup)
  char host[NI_MAXHOST] = "unknown";
  char service[NI_MAXSERV] = "unknown";
  int s = getnameinfo((struct sockaddr *) &serv_addr, sizeof(serv_addr), host, NI_MAXHOST, service, NI_MAXSERV, NI_NUMERICSERV);
  
  if (s != 0)
    fprintf(stderr, "getnameinfo: %s\n", gai_strerror(s));
  
  cout << "Connected to " << serv_addr_p << ":" << serv_port << endl;
  cout << "Host name: " << host << ", service: " << service << endl;
  
  // allocate new packets to send
  packet_t *pdu_array = new packet_t[num_packets];
  packet_t *pdu;
  size_t packet_size = sizeof(packet_t);
  
  // start logging for the flow
  gettimeofday(&timestamp, NULL);
  fprintf(logfp, "\nSTART FLOW %s:%s TIME %ld.%3.6ld BYTES %zu*%d=%zu\n", host, service, timestamp.tv_sec, timestamp.tv_usec, sizeof(packet_t), num_packets, sizeof(packet_t) * num_packets);
  fprintf(logfp, "SEQ,\t sent_time\n");
  
  unsigned int seq = 0;
  int i;
  ssize_t nsend, ntotal = 0;
  bool fail = false;
  
  // send each packet one after another
  for (i = 0; i < num_packets; i++) {
    pdu = &pdu_array[i];
    
    gettimeofday(&timestamp, NULL);
    pdu->seq = ++seq;
    pdu->seconds = timestamp.tv_sec;
    pdu->micros = timestamp.tv_usec;
    pdu->probe = probe;
    
    if ((nsend = send(sockfd, pdu, packet_size, MSG_MORE)) != packet_size) {
      // report problem
      warn("send");
      fail = true;
    } else {
      ntotal += nsend;
      
      // log the packet
      if (probe)
	fprintf(logfp, "%3.9u*,\t %ld.%3.6ld\n", pdu->seq, pdu->seconds, pdu->micros);
      else
	fprintf(logfp, "%3.9u,\t %ld.%3.6ld\n", pdu->seq, pdu->seconds, pdu->micros);
    }
  }

  // end tcp flow
  gettimeofday(&timestamp, NULL);
  fprintf(logfp, "END FLOW %s:%s TIME %ld.%3.6ld BYTES %zd\n", host, service, timestamp.tv_sec, timestamp.tv_usec, ntotal);

  // close the connection and the socket
  close(sockfd);
  
  delete pdu_array;
  
  return fail;
}


/* send_fromtrace: Send packets by reading from a file. */
int
send_fromtrace(char *serv_ip, int serv_port, char *tracefilepath, int max_flows) {
  
  // establish connection first
  struct sockaddr_in serv_addr;
  
  // open trace file
  FILE *fp = fopen(tracefilepath, "r");
  char line[10];
  char *endptr;
  long micros, micros_prev = 0;
  useconds_t sleep_duration;
  bool probe = false;
  bool probe_prev = false;
  char cc_protocol[10];
  int count = 0;
  int flow_count = 0;
  
  bool ret = false;
  bool fail = false;
  
  while (fgets(line, 10, fp) != NULL) {
    
    if ((max_flows != 0) && (flow_count == max_flows))
      break;

    // strip the line of asterisk if present (denotes "probe" packet)
    char *pos = NULL;
    if ((pos = strchr(line, '*')) != NULL) 
      *pos = '\0';
    
    probe = (pos != NULL);
    
    // detect valid entry in the line
    errno = 0;
    micros = strtol(line, &endptr, 10);
    
    if (errno != 0) {
      warn("strtol");
      ret = true;
      break;
    }
    
    if (line == endptr)
      // if empty line, just ignore and move on
      continue;
    
    // one more packet added to the flow
    count += 1;
    
    if ( (probe != probe_prev) || (micros != micros_prev) ) {
      
      // this defines a different flow with "count" number of packets
      if (probe_prev)
	strcpy(cc_protocol, "cubic"); // the default cc protocol
      else
	strcpy(cc_protocol, "ccp");
      //strcpy(cc_protocol, "cubic");
      
      flow_count += 1;
	      
      fail = send_const(serv_ip, serv_port, cc_protocol, count, probe_prev);
      ret = (ret | fail);
      
      sleep_duration = micros - micros_prev;
      
      if (sleep_duration > 0)
	// sleep for specified duration
	usleep(sleep_duration);
      
      count = 0;
    }
    
    // get ready for next iteration
    micros_prev = micros;
    probe_prev = probe;
  }
  
  cout << "Done sending trace." << endl;
  
  fclose(fp);
  
  return int(fail);
}



int main(int argc, char** argv)
{
  struct sockaddr_in serv_addr;

  // commandline arguments
  char serv_ip[256];
  int serv_port;
  char logfilename[256];
  int max_flows = 0;
  
  short genmethod = 0; // Shiva: method of generation of packets ("const" by default)

  // method 0: fixed number of packets
  int num_packets;
  bool probe;

  // method 3: file
  char *tracefilepath = NULL;
  
  // we have been using only the "--type file" option so far
  char usage_str[200];
  sprintf(usage_str, "Usage: %s <server IP> <port> <logfilename> --type {const <num_packets> <probe_mode> | file <filepath>} [--maxflows <max_flows>]\n", argv[0]);
  
  // Shiva: additional options for determining the manner of
  // generation of packets
  if ((argc != 8) && (argc != 9) && (argc != 10) && (argc != 11)) {
    puts(usage_str);
    exit(0);
  }
  
  // parse all commandline options
  sprintf(serv_ip, "%s", argv[1]);
  serv_port = atoi(argv[2]);
  sprintf(logfilename, "./%s", argv[3]);
  
  if (strcmp(argv[4], "--type") == 0) {
    if (strcmp(argv[5], "const") == 0) {
      num_packets = atoi(argv[6]);
      probe = bool(atoi(argv[7]));
      genmethod = 0;
    } else if (strcmp(argv[5], "file") == 0) {
      tracefilepath = argv[6];
      genmethod = 3;
    } else {
      puts(usage_str);
      exit(0);
    }
  } else {
    puts(usage_str);
    exit(0);
  }

  if ((argc == 10) || (argc == 11)) {
    if (strcmp(argv[argc-2], "--maxflows") != 0) {
      puts(usage_str);
      exit(0);
    }
    if ((max_flows = atoi(argv[argc-1])) < 0)
      max_flows = 0;
  }

  cout << "Packet size: " << sizeof(packet_t) << endl;
  cout << "Max flows: " << max_flows << endl;
  
  // open log file
  logfp = fopen(logfilename, "w");
  
  // choose input sending method based on options
  if (genmethod == 0) {
    
    char tcp_cc[10];
    if (probe)
      strcpy(tcp_cc, "cubic");
    else
      strcpy(tcp_cc, "ccp");
    //strcpy(tcp_cc, "cubic");
    
    if (send_const(serv_ip, serv_port, tcp_cc, num_packets, probe) != 0) 
      fprintf(stderr, "ABNORMAL TERMINATION: Something went wrong in send_const\n");
  }
  else if (genmethod == 3) {
    if (send_fromtrace(serv_ip, serv_port, tracefilepath, max_flows) != 0)
      fprintf(stderr, "ABNORMAL TERMINATION: Something went wrong in send_fromtrace\n");
  }
  
  fclose(logfp);
  
  return 0;
}
