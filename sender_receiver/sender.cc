#include "channel.hpp"

using namespace std;


//extern int errno;
//int err;
static FILE *logfp = NULL;
struct timeval timestamp;


/* three sending modes for sender */
union send_mode {
  unsigned int ttr;
  unsigned int n_blocks;
  char *tracefilepath;
};


/* connection parameters */
struct tcp_conn {
  int sockfd;
  struct sockaddr_in serv_addr;
  //char serv_addr_p[INET_ADDRSTRLEN];
  char host[NI_MAXHOST];
  char service[NI_MAXSERV];
};


/* follow all steps to setup the connection, set relevant socket options */
int
setup_tcp_connection(char *serv_ip, int serv_port, char *cc_protocol, struct tcp_conn *conn) {
  
  int ret = 0;
  
  if (conn == NULL) {
    cerr << "Cannot setup connection if \'conn\' is NULL!" << endl;
    return -1;
  }
  
  struct sockaddr_in *serv_addr = &(conn->serv_addr);
  
  // opening a tcp socket
  if ((conn->sockfd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
    //err(-1, "socket");
    ret = errno;
    perror("socket");
    return ret;
  }
  
  int enabled = 1;
  if ((setsockopt(conn->sockfd, SOL_SOCKET, SO_REUSEADDR, &enabled, sizeof(enabled)) != 0)) {
    //err(-1, "sockopt SO_REUSEADDR");
    ret = errno;
    perror("sockopt SO_REUSEADDR");
    close(conn->sockfd);
    return ret;
  }
  
  // set the TCP congestion control protocol to be used
  if (cc_protocol != NULL)
    if ((setsockopt(conn->sockfd, IPPROTO_TCP, TCP_CONGESTION, cc_protocol, strlen(cc_protocol)) != 0)) {
      //err(-1, "sockopt TCP_CONGESTION");
      ret = errno;
      perror("sockopt TCP_CONGESTION");
      close(conn->sockfd);
      return ret;
    }
  
  // initialize the server struct with server address info
  memset(serv_addr, 0, sizeof(*serv_addr));
  serv_addr->sin_family = AF_INET;
  serv_addr->sin_port = htons(serv_port);
  //serv_addr->sin_addr.s_addr = inet_addr(serv_ip);
  if (inet_pton(AF_INET, serv_ip, &(serv_addr->sin_addr)) <= 0) {
    //err(-1, "inet_pton");
    ret = errno;
    perror("inet_pton");
    close(conn->sockfd);
    return ret;
  }
  
  // connect to the server
  if (connect(conn->sockfd, (struct sockaddr *) serv_addr, sizeof(*serv_addr)) < 0) {
    //err(-1, "connect");
    ret = errno;
    perror("connect");
    close(conn->sockfd);
    return ret;
  }
  
  // report successful connection to server
  
  // // print server address and port
  // if (inet_ntop(AF_INET, &(serv_addr->sin_addr), conn->serv_addr_p, INET_ADDRSTRLEN) == NULL) {
  //   warn("inet_ntop");
  //   strcpy(conn->serv_addr_p, serv_ip);
  // }
  
  // print host name and service (DNS lookup) (if possible and available)
  int s = getnameinfo((struct sockaddr *) serv_addr, sizeof(*serv_addr), conn->host, NI_MAXHOST, conn->service, NI_MAXSERV, NI_NUMERICSERV);
  if (s != 0) {
    cerr << "getnameinfo: " << gai_strerror(s) << endl;
    strcpy(conn->host, serv_ip);
    sprintf(conn->service, "%d", serv_port);
  }
  
  cout << "Connected to " << serv_ip << ":" << serv_port << endl;
  cout << "Host name: " << conn->host << ", service: " << conn->service << endl;
  
  return ret;
}


/* print total bytes transferred, rounded to KiB or MiB or GiB as
   appropriate */
void print_bytes_nice(long ntotal) {
  
  float ntotal_nice;
  long kibi = 1024;
  char unit[4] = "B";
  
  if (ntotal < kibi) 
    ntotal_nice = ntotal;
  else if (ntotal < (kibi << 10)) {
    ntotal_nice = float(ntotal) / kibi;
    strcpy(unit, "KiB");
  } else if (ntotal < (kibi << 20)) {
    ntotal_nice = float(ntotal) / (kibi << 10);
    strcpy(unit, "MiB");
  } else if (ntotal < (kibi << 30)) {
    ntotal_nice = float(ntotal) / (kibi << 20);
    strcpy(unit, "GiB");
  }
  
  cout << "Transferred a total of " << ntotal_nice << " " << unit << endl;
}


/* send_ttr: keep sending a block of packets for 'ttr' seconds. */
int
send_ttr(struct tcp_conn *conn, unsigned int ttr, unsigned int blksize, bool probe) {
  
  // TODO: communicate the blocksize
  
  // allocate new packets to send
  packet_t *block = new packet_t[blksize];
  
  // record start timestamp
  gettimeofday(&timestamp, NULL);
  time_t start_s = timestamp.tv_sec;
  
  // start logging for the flow
  if (logfp) {
    fprintf(logfp, "\nSTART SEND %s:%s TIME %ld.%.6ld TTR %d seconds\n", conn->host, conn->service, timestamp.tv_sec, timestamp.tv_usec, ttr);
    fprintf(logfp, "%9s, %11s, %18s\n", "SEQ", "sent_bytes", "sent_time");
  }
  
  unsigned int seq = 0;
  int i;
  ssize_t nsend, ntotal = 0;
  bool fail = false;
  
  do {
    
    seq++;
    
    gettimeofday(&timestamp, NULL);
    
    for (i = 0; i < blksize; i++) {
      block[i].seq = seq;
      block[i].seconds = timestamp.tv_sec;
      block[i].micros = timestamp.tv_usec;
      block[i].probe = probe;
    }
    
    // send all packets in one shot
    if ((nsend = send(conn->sockfd, block, blksize * PACKET_SIZE, 0)) != (blksize * PACKET_SIZE)) {
      // report problem
      warn("send");
      fail = true;
    } else {
      ntotal += nsend;
      // log the send
      if (logfp)
	fprintf(logfp, "%09u, %11zd, %11ld.%.6ld\n", seq, nsend, timestamp.tv_sec, timestamp.tv_usec);
    }
    
    gettimeofday(&timestamp, NULL);
    
  } while ((timestamp.tv_sec - start_s) < ttr);
  
  // end tcp flow
  //gettimeofday(&timestamp, NULL);
  if (logfp)
    fprintf(logfp, "END SEND %s:%s TIME %ld.%.6ld BYTES %zd\n", conn->host, conn->service, timestamp.tv_sec, timestamp.tv_usec, ntotal);
  
  print_bytes_nice((long) ntotal);
  
  // close the connection and the socket
  // close(sockfd);
  
  delete block;
  
  return int(fail);
}


/* send_nblocks: send specified number of blocks of packets. */
int
send_nblocks(struct tcp_conn *conn, int n_blocks, unsigned int blksize, bool probe) {
  
  // TODO: communicate the blocksize
  
  // allocate new packets to send
  packet_t *block = new packet_t[blksize];
  
  // record start timestamp
  gettimeofday(&timestamp, NULL);
  
  // start logging for the flow
  if (logfp) {
    fprintf(logfp, "\nSTART SEND %s:%s TIME %ld.%.6ld DATA %zu*%u=%zu KiB\n", conn->host, conn->service, timestamp.tv_sec, timestamp.tv_usec, PACKET_SIZE, blksize, PACKET_SIZE * blksize);
    fprintf(logfp, "%9s, %11s, %18s\n", "SEQ", "sent_bytes", "sent_time");
  }
  
  unsigned int seq;
  int i;
  ssize_t nsend, ntotal = 0;
  bool fail = false;
  
  for (seq = 1; seq <= n_blocks; seq++) {
    
    gettimeofday(&timestamp, NULL);

    for (i = 0; i < blksize; i++) {
      block[i].seq = seq;
      block[i].seconds = timestamp.tv_sec;
      block[i].micros = timestamp.tv_usec;
      block[i].probe = probe;
    }
    
    // send all packets in one shot
    if ((nsend = send(conn->sockfd, block, blksize * PACKET_SIZE, 0)) != (blksize * PACKET_SIZE)) {
      // report problem
      warn("send");
      fail = true;
    } else {
      ntotal += nsend;
      // log the send
      if (logfp)
	fprintf(logfp, "%09u, %11zd, %11ld.%.6ld\n", seq, nsend, timestamp.tv_sec, timestamp.tv_usec);
    }
  }
  
  // end tcp flow
  gettimeofday(&timestamp, NULL);

  if (logfp)
    fprintf(logfp, "END SEND %s:%s TIME %ld.%.6ld BYTES %zd\n", conn->host, conn->service, timestamp.tv_sec, timestamp.tv_usec, ntotal);
  
  print_bytes_nice((long) ntotal);
  
  // close the connection and the socket
  // close(sockfd);
  
  delete block;
  
  return int(fail);
}


/* send_fromtrace: Send packets by reading from a file. */
int
send_fromtrace(struct tcp_conn *conn, char *tracefilepath) {
  
  // TODO: communicate the blocksize, which is PACKET_SIZE in this case
  
  // open trace file
  FILE *fp = fopen(tracefilepath, "r");
  char line[10];
  char *endptr;
  long micros, micros_prev = 0;
  useconds_t sleep_duration;
  bool probe = false;
  bool probe_prev = false;
  //char cc_protocol[10];
  int count = 0;
  //int flow_count = 0;
  
  packet_t *block;
  unsigned int seq = 0;
  int i;
  ssize_t nsend, ntotal = 0;
  
  bool ret = false;
  bool fail = false;
  
  // record start timestamp
  gettimeofday(&timestamp, NULL);
  
  // start logging for the flow
  if (logfp) {
    fprintf(logfp, "\nSTART SEND %s:%s TIME %ld.%.6ld FILE %s\n", conn->host, conn->service, timestamp.tv_sec, timestamp.tv_usec, tracefilepath);
    fprintf(logfp, "%9s, %11s, %18s\n", "SEQ", "sent_bytes", "sent_time");
  }
  
  while (fgets(line, 10, fp) != NULL) {
    
    //if ((max_flows != 0) && (flow_count == max_flows))
    //  break;
    
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
      //if (probe_prev)
      //	strcpy(cc_protocol, "cubic"); // the default cc protocol
      //else
      //	strcpy(cc_protocol, "ccp");
      //strcpy(cc_protocol, "cubic");
      
      //flow_count += 1;
      
      //fail = send_const(serv_ip, serv_port, cc_protocol, count, probe_prev, bulk);
      
      // this defines a new block of data
      block = new packet_t[count];
      
      seq++;
      
      gettimeofday(&timestamp, NULL);
      
      for (i = 0; i < count; i++) {
	block[i].seq = seq;
	block[i].seconds = timestamp.tv_sec;
	block[i].micros = timestamp.tv_usec;
	block[i].probe = probe_prev;
      }
      
      // send all packets in one shot
      if ((nsend = send(conn->sockfd, block, count * PACKET_SIZE, 0)) != (count * PACKET_SIZE)) {
	// report problem
	warn("send");
	fail = true;
      } else {
	ntotal += nsend;
	// log the send
	if (logfp)
	  fprintf(logfp, "%09u, %11zd, %11ld.%.6ld\n", seq, nsend, timestamp.tv_sec, timestamp.tv_usec);
      }
      
      delete block;
      
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
  
  gettimeofday(&timestamp, NULL);

  if (logfp)
    fprintf(logfp, "END SEND %s:%s TIME %ld.%.6ld BYTES %zd\n", conn->host, conn->service, timestamp.tv_sec, timestamp.tv_usec, ntotal);
  
  print_bytes_nice((long) ntotal);
  
  cout << "Done sending trace." << endl;
  
  fclose(fp);
  
  return int(ret);
}


int main(int argc, char** argv)
{
  // commandline arguments
  char *serv_ip;
  int serv_port;
  
  // options
  send_mode mode;
  mode.ttr = 10;
  unsigned int blksize =   128; // in kibibytes (multiple of PACKET_SIZE)
  char *cc_algo        =  NULL; // the cc algorithm to use
  char *logfilepath    =  NULL; // path to log file (optional)
  bool verbose         = false; // whether to show verbose output (log the output of sender)
  
  // Shiva: method of generation of packets ("const" by default)
  int genmethod = 0;
  
  // parse the commandline arguments and options
  int opt;
  char usage_str[200];
  sprintf(usage_str, "Usage: %s [-t ttr / -n n_blks / -f tracefilepath] [-b blksize] [-C cc_algo] [-l logfilepath] [-v] SERVER_IP SERVER_PORT\n", argv[0]);
  
  while ((opt = getopt(argc, argv, "t:n:f:b:C:l:v")) != -1) {
    switch (opt) {
    case 't':
    case 'n':
    case 'f':
      if (genmethod == 0) {
	genmethod = opt;
	if (opt == 't')
	  mode.ttr = atoi(optarg);
	else if (opt == 'n')
	  mode.n_blocks = atoi(optarg);
	else
	  mode.tracefilepath = optarg;
      } else {
	cerr << "Only one of \'-t\', \'-n\' and \'-f\' is allowed." << endl;
	cerr << usage_str << endl;
	exit(EXIT_FAILURE);
      }
      break;
    case 'b':
      blksize = atoi(optarg);
      if (blksize < 1) {
	cerr << "Block size (-b option) has to be > 1." << endl;
	exit(EXIT_FAILURE);
      }
      break;
    case 'C':
      cc_algo = optarg;
      break;
    case 'l':
      logfilepath = optarg;
      // open log file
      if (!(logfp = fopen(logfilepath, "w"))) {
	cerr << "Unable to access " << logfilepath << "." << endl;
	exit(EXIT_FAILURE);
      }
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
  
  // set up connections
  struct tcp_conn conn;
  
  if (setup_tcp_connection(serv_ip, serv_port, cc_algo, &conn) != 0) {
    cerr << "setup_tcp_connection() failed!" << endl;
    exit(EXIT_FAILURE);
  }
  
  // choose input sending method based on options
  if (genmethod == 'n') {
    if (send_nblocks(&conn, mode.n_blocks, blksize, 0) != 0) 
      cerr << "ABNORMAL TERMINATION: Something went wrong in send_nblocks()" << endl;
  } else if (genmethod == 'f') {
    if (send_fromtrace(&conn, mode.tracefilepath) != 0)
      cerr << "ABNORMAL TERMINATION: Something went wrong in send_fromtrace()" << endl;
  } else {
    // the default option in case no other sending mode is specified
    if (send_ttr(&conn, mode.ttr, blksize, 0) != 0)
      cerr << "ABNORMAL TERMINATION: Something went wrong in send_ttr()" << endl;
  }
  
  // finally, close connection
  cout << "Done, closing connection." << endl;
  
  close(conn.sockfd);
  
  if (logfp)
    fclose(logfp);
  
  return 0;
}
