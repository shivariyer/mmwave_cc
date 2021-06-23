#include "channel.hh"

using namespace std;

static int quit = 0;

// SIGINT handler: set quit to 1 for graceful termination 
void
handle_sigint(int signum) {
  quit = 1;
}

int main(int argc, char **argv)
{
  // commandline arguments
  int port;

  // options
  char log_suffix[20];
  log_suffix[0] = '\0';
  
  // parse the commandline arguments and options
  int opt;
  char usage_str[200];
  sprintf(usage_str, "Usage: %s PORT [-s savesuffix]", argv[0]);
  
  while ((opt = getopt(argc, argv, "s:")) != -1) {
    switch (opt) {
    case 's':
      strcpy(log_suffix, optarg);
      break;
    default:
      cerr << usage_str << endl;
      exit(EXIT_FAILURE);
    }
  }
  
  // finally, get the mandatory arguments
  if (optind != argc-1) {
    cerr << "One mandatory argument expected: port number." << endl;
    cerr << usage_str << endl;
    exit(EXIT_FAILURE);
  }
  
  port = atoi(argv[optind]);

  int nrecv, nsend;
  struct sockaddr_in bind_addr;
  struct sockaddr_in client_addr;
  socklen_t client_addr_len;
  
  // creating the remote struct for sending the packet initialization from the user side
  int ret = 0;

  int sockfd; 
  if ((sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
    ret = errno;
    perror("socket");
    return ret;
  }

  int enable = 1;
  if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof (enable)) != 0) {
    ret = errno;
    perror("sockopt SO_REUSEADDR");
    close(sockfd);
    return ret;
  }

  // bind the socket to the the port number
  memset(&bind_addr, 0, sizeof(bind_addr));
  bind_addr.sin_family = AF_INET;
  bind_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  bind_addr.sin_port = htons(port);

  if (bind(sockfd, (struct sockaddr *) &bind_addr, sizeof(bind_addr)) < 0) {
    ret = errno;
    perror("bind");
    close(sockfd);
    return ret;
  }

  // do not restart the recvfrom() system call when INTterrupted
  struct sigaction sigact;
  sigact.sa_handler = handle_sigint;
  sigact.sa_flags = 0;
  sigaction(SIGINT, &sigact, NULL);

  // initialize the start time
  if (strlen(log_suffix) == 0) {
    time_t t = time(NULL);
    struct tm *loctm = localtime(&t);
    strftime(log_suffix, sizeof(log_suffix), "%Y%m%d_%H%M", loctm);
  } 
  
  // start logging
  char logfilepath[100];
  sprintf(logfilepath, "receiver_%s.log", log_suffix);
  FILE *logfp = fopen(logfilepath, "w");
  fprintf(logfp, "host,port,seq,bytes,time_sent,time_recv\n");

  char client_addr_p[INET_ADDRSTRLEN] = "X.X.X.X";

  struct timeval timestamp;
  udp_packet_t pdu_data;
  udp_ack_t pdu_ack;
  
  while ( !quit ) {

    // receive a packet from user
    if ((nrecv = recvfrom(sockfd, &pdu_data, PACKET_SIZE, 0, (struct sockaddr *) &client_addr, &client_addr_len)) >= 0) {

      gettimeofday(&timestamp,NULL);

      // send an ACK back
      pdu_ack.seq = pdu_data.seq;
      pdu_ack.bytes = nrecv;
      pdu_ack.seconds = timestamp.tv_sec;
      pdu_ack.micros = timestamp.tv_usec;

      if ((nsend = sendto(sockfd, &pdu_ack, sizeof(pdu_ack), 0, (struct sockaddr *) &client_addr, client_addr_len)) == -1)
	warn("error sending ack packet seq %u", pdu_ack.seq);

      if (inet_ntop(AF_INET, &client_addr.sin_addr, client_addr_p, INET_ADDRSTRLEN) == NULL) 
	warn("inet_ntop");

      fprintf(logfp, "%s,%u,%d,%d,%ld.%06ld,%ld.%06ld\n", client_addr_p, ntohs(client_addr.sin_port), pdu_data.seq, nrecv, pdu_data.seconds, pdu_data.micros, timestamp.tv_sec, timestamp.tv_usec);
    } else {
      if (errno == EINTR) {
	cout << "Receiver has been interrupted." << endl;
	break;
      } else
	warn("error receiving packet");
    }
  }

  fflush(logfp);

  fclose(logfp);

  close(sockfd);

  cout << "Finished the experiment." << endl;
  
  return 0;
}
