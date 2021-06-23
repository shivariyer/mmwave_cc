#include <map>
#include <pthread.h>

#include "channel.hh"

using namespace std;


// some of the variables that are shared between main thread and
// recving thread are made static global
static int sockfd;
static FILE *sentlog_fp;
static FILE *rtlog_fp;

static int quit = 0;
static map<int, struct timeval> pkts_tab;
static pthread_mutex_t pkts_tab_lock;

// a constant
static struct timeval TIMESTAMP_INIT;

// recving_thread: receive acks, remove entry from pkts table, and log
// the packet
void*
recving_thread (void *arg) {

  int nrecv;

  // sent time, received time (at receiver) and final time at end of roundtrip
  struct timeval time_sent, time_recv, time_rt;
  udp_ack_t pdu_ack;
  int ack_pkt_size = sizeof(udp_ack_t);

  while (!quit) {
    
    if ((nrecv = recv(sockfd, &pdu_ack, ack_pkt_size, 0)) >= 0) {

      // pull all data for logging
      gettimeofday(&time_rt,NULL);
      time_recv.tv_sec = pdu_ack.seconds;
      time_recv.tv_usec = pdu_ack.micros;

      // remove from list
      pthread_mutex_lock(&pkts_tab_lock);
      time_sent.tv_sec = (pkts_tab.at(pdu_ack.seq)).tv_sec;
      time_sent.tv_usec = (pkts_tab.at(pdu_ack.seq)).tv_usec;
      pkts_tab.erase(pdu_ack.seq);
      pthread_mutex_unlock(&pkts_tab_lock);

      // log the info
      fprintf(rtlog_fp, "%d,%lu,%ld.%06ld,%ld.%06ld,%ld.%06ld\n", pdu_ack.seq, pdu_ack.bytes, time_sent.tv_sec, time_sent.tv_usec, time_recv.tv_sec, time_recv.tv_usec, time_rt.tv_sec, time_rt.tv_usec);
    } else {
      if (errno == EINTR) {
	cout << "Recving thread is interrupted." << endl;
	break;
      } else
	warn("error receiving packet");
    }
  }

  fflush(rtlog_fp);
  sync();

  return 0;
}


// send_const: send packets a constant bit rate, with optional bursts 
int
send_const(int ttr, int maxbw) {
  
  // initialize lock
  pthread_mutex_init(&pkts_tab_lock, NULL);

  // create the receiving thread
  pthread_t recving_tid;
  if (pthread_create(&recving_tid, NULL, &recving_thread, NULL) != 0) {
    warn("pthread_create");
    return -1;
  }
  
  // allocate new packet to send (pkt_size should be equal to
  // the constant value PACKET_SIZE)
  udp_packet_t pdu;
  size_t pkt_size = sizeof(udp_packet_t);

  // number of packets per second (if limit on bw is specified)
  float pps = (maxbw * 1e6 / 8) / PACKET_SIZE;
  float sleep_micros = 1e6 / pps;

  int seq = 0;
  int nsend;
  short fail = 0;

  struct timeval timestamp;

  for (seq = 1;; seq++) {
    
    pdu.seq = seq;
    gettimeofday(&timestamp,NULL);
    pdu.seconds = timestamp.tv_sec;
    pdu.micros = timestamp.tv_usec;
      
    // sending pkt and adding entry into table together should be
    // an atomic operation, so that the recving_thread does not
    // refer a non-existent seq no in the table after having seen
    // the ack pkt. Hence hold lock before sending and putting
    // into table.
    pthread_mutex_lock(&pkts_tab_lock);
      
    if ((nsend = send(sockfd, &pdu, pkt_size, 0)) == pkt_size) {
      pkts_tab.insert( {seq, timestamp} );
    } else {
      cerr << "sending error";
      fail = 1;
    }
    
    pthread_mutex_unlock(&pkts_tab_lock);

    fprintf(sentlog_fp, "%d,%lu,%ld.%06ld\n", seq, pkt_size, timestamp.tv_sec, timestamp.tv_usec);
    
    // terminating conditions
    if (fail)
      break;

    // pace the sending if limit on bw is specified
    if (pps)
      usleep(sleep_micros);

    if(timestamp.tv_sec - TIMESTAMP_INIT.tv_sec > ttr)
      break;
  }

  // kill the receiving thread
  cout << "waiting for recving_thread..." << endl;
  quit = 1;
  // if (pthread_join(recving_tid, NULL) != 0)
  //   warn("pthread_join");

  // timed join
  struct timespec abstime;
  clock_gettime(CLOCK_REALTIME, &abstime);
  abstime.tv_sec += 2*ttr;
  if (pthread_timedjoin_np(recving_tid, NULL, &abstime) != 0) {
    cout << "child thread failed to join, so cancelling it..." << endl;
    if (pthread_cancel(recving_tid) != 0)
      warn("pthread_cancel");
    if (pthread_join(recving_tid, NULL) != 0)
      warn("pthread_join");

    // gettimeofday(&timestamp, NULL);
    // printf("%ld.%06ld\n", timestamp.tv_sec, timestamp.tv_usec);
    fflush(rtlog_fp);
  }

  cout << "done." << endl;
  
  return fail;
}


int main(int argc, char **argv)
{
  // commandline arguments
  char *serv_ip;
  int serv_port;

  // options
  int ttr = 10;
  int maxbw = 0;
  char log_suffix[20];
  log_suffix[0] = '\0';
  bool verbose = false; // whether to show verbose output (log the output of sender)

  // parse the commandline arguments and options
  int opt;
  char usage_str[200];
  sprintf(usage_str, "Usage: %s SERVER_IP SERVER_PORT [-t ttr] [-b maxbw_Mbps] [-s savesuffix] [-v]", argv[0]);
  
  while ((opt = getopt(argc, argv, "t:b:s:v")) != -1) {
    switch (opt) {
    case 't':
      ttr = atoi(optarg);
      break;
    case 'b':
      maxbw = atoi(optarg);
      break;
    case 's':
      strcpy(log_suffix, optarg);
      break;
    case 'v':
      verbose = true;
      break;
    default:
      cerr << usage_str << endl;
      exit(EXIT_FAILURE);
    }
  }
  
  // finally, get the mandatory arguments
  if (optind != argc-2) {
    cerr << "Two mandatory arguments expected: server IP address and server port." << endl;
    cerr << usage_str << endl;
    exit(EXIT_FAILURE);
  }
  
  serv_ip = argv[optind];
  serv_port = atoi(argv[optind+1]);

  int ret = 0;
  
  // open a UDP socket
  if ((sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    err(-1, "socket");

  int enable = 1;
  if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof (enable)) == -1) {
    ret = errno;
    perror("sockopt SO_REUSEADDR");
    close(sockfd);
    return ret;
  }

  // set the server address struct with IP addr and port info
  struct sockaddr_in serv_addr;
  memset(&serv_addr, 0, sizeof(serv_addr));
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(serv_port);
  if (inet_pton(AF_INET, serv_ip, &(serv_addr.sin_addr)) <= 0) {
    ret = errno;
    perror("inet_pton");
    close(sockfd);
    return ret;
  }

  // bind the sockfd to the server address so that packets
  // can be sent using send() instead of sendto()
  if (connect(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
    ret = errno;
    perror("connect");
    close(sockfd);
    return ret;
  }

  // initialize the start time
  if (strlen(log_suffix) == 0) {
    time_t t = time(NULL);
    struct tm *loctm = localtime(&t);
    strftime(log_suffix, sizeof(log_suffix), "%Y%m%d_%H%M", loctm);
  } 
  
  // initialize log file paths
  char sentlog_filename[100]; 
  sprintf(sentlog_filename, "sender_%s.log", log_suffix);
  sentlog_fp = fopen(sentlog_filename, "w");

  char rtlog_filename[100];
  sprintf(rtlog_filename, "roundtrip_%s.log", log_suffix);
  rtlog_fp = fopen(rtlog_filename, "w");

  cout << "Logging sender output to \'" << sentlog_filename << "\' and roundtrip output to \'" << rtlog_filename << "\'" << endl;

  // start logging
  gettimeofday(&TIMESTAMP_INIT,NULL);
  fprintf(sentlog_fp, "START TIMESTAMP %ld.%06ld\n", TIMESTAMP_INIT.tv_sec, TIMESTAMP_INIT.tv_usec); 
  fprintf(sentlog_fp, "seq,bytes,time_sent\n");

  fprintf(rtlog_fp, "START TIMESTAMP %ld.%06ld\n", TIMESTAMP_INIT.tv_sec, TIMESTAMP_INIT.tv_usec); 
  fprintf(rtlog_fp, "seq,bytes,time_sent,time_recv,time_rt\n");

  // choose input sending method based on options
  if (send_const(ttr, maxbw) != 0) 
    fprintf(stderr, "ABNORMAL TERMINATION: Something went wrong in send_const\n");

  struct timeval timestamp;
  gettimeofday(&timestamp,NULL);
  fprintf(sentlog_fp, "END TIMESTAMP %ld.%06ld\n", timestamp.tv_sec, timestamp.tv_usec);
  fprintf(rtlog_fp, "END TIMESTAMP %ld.%06ld\n", timestamp.tv_sec, timestamp.tv_usec);

  close(sockfd);

  fclose(rtlog_fp);

  fclose(sentlog_fp);
  
  return 0;
}
