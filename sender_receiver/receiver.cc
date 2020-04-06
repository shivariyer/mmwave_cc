#include "channel.hpp"

using namespace std;

//#define PORT 4311

static int quit = 0;
// static FILE *fp;
// static int sockfd;

/* SIGINT handler: set quit to 1 for graceful termination */
void
handle_sigint(int signum) {
  quit = 1;
  cout << "PID: " << getpid() << ", received signal " << signum << endl;
  // close(sockfd);
  // exit(1);
  return;
}


/* SIGCHLD handler: wait for terminated child processes and then
   return, so that zombie processes do not remain. */
void
handle_sigchld(int signum) {
  
  pid_t pid;
  int   stat;
  
  while ( (pid = waitpid(-1, &stat, WNOHANG)) > 0 );
    // cout << "Server child " << pid << " terminated." << endl;
  
  return;
}


/* Subtract the ‘struct timeval’ values X and Y,
   storing the result in RESULT.
   Return 1 if the difference is negative, otherwise 0. */
int
timeval_subtract (struct timeval *result, struct timeval *x, struct timeval *y)
{
  // Perform the carry for the later subtraction
  long y_sec = y->tv_sec, y_usec = y->tv_usec;
  
  if (x->tv_usec < y_usec) {
    int nsec = (y_usec - x->tv_usec) / 1000000 + 1;
    y_usec -= 1000000 * nsec;
    y_sec += nsec;
  }
  if (x->tv_usec - y_usec > 1000000) {
    int nsec = (x->tv_usec - y_usec) / 1000000;
    y_usec += 1000000 * nsec;
    y_sec -= nsec;
  }
  
  // now subtract
  result->tv_sec = x->tv_sec - y_sec;
  result->tv_usec = x->tv_usec - y_usec;
  
  // Return 1 if result is negative. 
  return x->tv_sec < y_sec;
}


int main(int argc, char**argv)
{
  // *** constants ***
  const int N_CLIENTS_MAX_LIMIT = 10000;
  
  // *** list of mandatory arguments to the program ***
  
  // port at which the receiver should listen
  int PORT;
  
  // we will accept only these many connections at max, and then the server will exit
  int n_clients_max;
  
  // file name for logging
  char filename[64];
  
  // should we log progress on the console?
  bool verbose = false;
  
  // should we log packets on the receiver side?
  bool log = false;
  
  //float delay;
  struct sockaddr_in bind_addr;
  struct sockaddr_in client_addr;
  socklen_t client_addr_len;
  int sockfd;
  int sockfd_client;
  
  struct timeval cur_time;
  
  packet_t pdu_data;
  
  char proc_prefix[20];
  sprintf(proc_prefix, "Server (%d)> ", getpid());
  
  char usage_str[200];
  sprintf(usage_str, "Usage: %s <port> <maxclients> <verbose> [--log <logfilenameprefix>]", argv[0]);
  
  if ((argc != 4) && (argc != 6)) {
    cout << usage_str << endl;
    return 1;
  }
  
  // parse all commandline arguments
  PORT = atoi(argv[1]);
  n_clients_max = atoi(argv[2]);
  if (n_clients_max < 0 || n_clients_max > N_CLIENTS_MAX_LIMIT) {
    cerr << proc_prefix << "n_clients_max should be between 0 and " << N_CLIENTS_MAX_LIMIT << "!" << endl;
    return -2;
  }
  verbose = bool(atoi(argv[3]));
  
  if (argc == 6) {
    if (strcmp(argv[4], "--log") == 0) {
      log = true;
      sprintf(filename, "./%s", argv[5]);
    }
    else {
      cout << usage_str << endl;
      return 1;
    }
  }
  
  // creating the remote struct for sending the packet initialization from the user side
  sockfd = socket(AF_INET, SOCK_STREAM, 0);
  
  int enable = 1;
  if ( (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof (enable)) != 0) ||
       (setsockopt(sockfd, SOL_SOCKET, SO_REUSEPORT, &enable, sizeof(enable)) != 0) ) 
    err(-1, "sockopt");
  
  // bind the socket to the the port number
  memset(&bind_addr, 0, sizeof(bind_addr));
  bind_addr.sin_family = AF_INET;
  bind_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  bind_addr.sin_port = htons(PORT);
  
  if (bind(sockfd, (struct sockaddr *)&bind_addr, sizeof(bind_addr)) < 0)
    err(-1, "bind");
  
  // set the socket as "passive" (i.e. listening)
  listen(sockfd, LISTENQ);
  
  // set up interrupt handlers for graceful termination
  struct sigaction sigact_int, sigact_chld;
  
  // to handle keyboard interruption
  sigact_int.sa_handler = handle_sigint;
  //sigact_int.sa_flags = SA_RESETHAND;
  sigaction(SIGINT, &sigact_int, NULL);
  
  // to handle child termination
  sigact_chld.sa_handler = handle_sigchld;

  // set the mask and restart flag according to p.130 in UNIX Network
  // Programming by W. Richard Stevens, et. al, 3rd edition
  sigemptyset(&sigact_chld.sa_mask);
  sigact_chld.sa_flags = SA_RESTART;
  sigaction(SIGCHLD, &sigact_chld, NULL);
  
  int n_clients = 0;
  while ( !quit && ((n_clients < n_clients_max) || (n_clients_max == 0)) ) {
    
    // listen for connections
    if (verbose) {
      if (n_clients_max == 0)
	cout << proc_prefix << "Listening for connections ..." << endl;
      else
	cout << proc_prefix << "Listening for remaining " << n_clients_max - n_clients << "/" << n_clients_max << " connections ..." << endl;
    }
    
    client_addr_len = sizeof(struct sockaddr_storage);
    
    // accept() system call seems to return < 0 when interrupted
    // (i.e. it is not automatically restarted upon return from
    // a signal handler)
    if ((sockfd_client = accept(sockfd, (struct sockaddr *) &client_addr, &client_addr_len)) < 0) {
      
      // this is necessary, because when child terminates, it sends a
      // SIGCHLD to the parent while the parent is sleeping on
      // accept(), which is treated as an "interruption", causing
      // accept() to return with errno equal to EINTR (hence EINTR
      // does NOT necessarily indicate SIGINT)
      if (errno == EINTR)
	continue;
      
      // if any other signal was sent, terminate immediately
      cerr << proc_prefix << "accept(): " << strerror(errno) << endl;
      break;
    }
    
    // print client ip and port
    char client_addr_p[INET_ADDRSTRLEN] = "X.X.X.X";
    if (inet_ntop(AF_INET, &client_addr.sin_addr, client_addr_p, INET_ADDRSTRLEN) == NULL) 
      cerr << proc_prefix << "inet_ntop(): " << strerror(errno) << endl;
    
    // print host name and service (DNS lookup)
    char host[NI_MAXHOST] = "unknown";
    char service[NI_MAXSERV] = "unknown";
    int s = getnameinfo((struct sockaddr *) &client_addr, client_addr_len, host, NI_MAXHOST, service, NI_MAXSERV, NI_NUMERICSERV);
    
    if (s != 0)
      cerr << proc_prefix << "getnameinfo(): " << gai_strerror(s);
    
    // accepted connection successfully, ready to start sending data
    n_clients += 1;
    
    if (verbose) {
      cout << proc_prefix << "Accepted connection from " << client_addr_p << ":" << ntohs(client_addr.sin_port) << endl;
      cout << proc_prefix << "Host name: " << host << ", service: " << service << endl;
    }
    
    pid_t pid;
    if ((pid = fork()) == 0) {
      
      // ** NO PRINTING TO CONSOLE INSIDE CHILD PROCESS **
      
      close(sockfd);
      
      sprintf(proc_prefix, "Child (%d)> ", getpid());
      
      time_t cur_time_secs;
      struct tm *cur_time_fmt;
      FILE *fp;
      if (log) {
	cur_time_secs = time(NULL);
	cur_time_fmt = localtime(&cur_time_secs);
	sprintf(filename,
		"%s_%05d_%4d%02d%02d%02d%02d.log",
		filename,
		getpid(),
		1900 + cur_time_fmt->tm_year,
		cur_time_fmt->tm_mon+1,
		cur_time_fmt->tm_mday,
		cur_time_fmt->tm_hour,
		cur_time_fmt->tm_min);
	fp = fopen(filename, "w");
      }
      
      // tcp flow started
      if (log) {
	gettimeofday(&cur_time, NULL);
	fprintf(fp, "\nSTART FLOW from %s:%s at TIME %ld.%.6ld\n", host, service, cur_time.tv_sec, cur_time.tv_usec);
	fprintf(fp, "%9s, %11s, %18s, %18s, %9s\n", "SEQ", "recv_bytes", "recv_time", "sent_time", "delay_s");
      }
      
      if (verbose)
	cout << proc_prefix << "Flow has started." << endl;
      
      unsigned int seq = 1;
      unsigned int seq_count = 0;
      struct timeval sent_time, recv_time, delay;
      ssize_t nrecv, ntotal = 0;
      
      // receive data from user (MSG_WAITALL ensures that all the data
      // is read even if the process is INTerrupted)
      while ((nrecv = recv(sockfd_client, &pdu_data, PACKET_SIZE, MSG_WAITALL)) > 0) {
	//cout << proc_prefix << "Received a packet" << endl;
	
	// // log each packet
	// if (log) {
	//   ntotal += nrecv;
	//   gettimeofday(&cur_time,NULL);
	//   delay = (cur_time.tv_sec - pdu_data.seconds) + (cur_time.tv_usec - pdu_data.micros) / 1e6;
	//   fprintf(fp, "%3.9u, %zd, %ld.%3.6ld, %ld.%3.6ld, %f\n", pdu_data.seq, nrecv, cur_time.tv_sec, cur_time.tv_usec, pdu_data.seconds, pdu_data.micros, delay);
	// }
	
	// log each block instead
	if (log) {
	  // record when this packet is received
	  gettimeofday(&recv_time, NULL);
	  ntotal += nrecv;
	  
	  // WARNING: we assume that seq numbers start at 1 (sent_time
	  // is uninitialized when the first ever packet is received,
	  // so if the following condition is true for the very first
	  // packet, then that log line will have undefined values)
	  
	  if (pdu_data.seq > seq) {
	    // delay is computed using recorded sent_time and
	    // recv_time for last packet of previous block (seq)
	    timeval_subtract(&delay, &recv_time, &sent_time);
	    //fprintf(fp, "%3.9u, %zu, %ld.%3.6ld, %ld.%3.6ld, %f\n", seq, seq_count * PACKET_SIZE, recv_time.tv_sec, recv_time.tv_usec, sent_time.tv_sec, sent_time.tv_usec, (delay.tv_sec + (delay.tv_usec * 1e-6)));
	    fprintf(fp, "%09u, %11zu, %11ld.%.6ld, %11ld.%.6ld, %9.6f\n", seq, seq_count * PACKET_SIZE, recv_time.tv_sec, recv_time.tv_usec, sent_time.tv_sec, sent_time.tv_usec, (delay.tv_sec + (delay.tv_usec * 1e-6)));	    
	    // reset seq counter
	    seq = pdu_data.seq;
	    seq_count = 1;
	  } else seq_count++;
	  
	  sent_time.tv_sec = pdu_data.seconds;
	  sent_time.tv_usec = pdu_data.micros;
	}
      }
      
      if (nrecv < 0 || errno == EINTR)
	cerr << proc_prefix << "recv(): " << strerror(errno) << endl;
      else if (verbose)
	cout << proc_prefix << "Flow has ended." << endl;
      
      // tcp flow ended
      if (log) {
	// log the last block (boundary condition)
	timeval_subtract(&delay, &recv_time, &sent_time);
	//fprintf(fp, "%3.9u, %zu, %ld.%3.6ld, %ld.%3.6ld, %f\n", seq, seq_count * PACKET_SIZE, recv_time.tv_sec, recv_time.tv_usec, sent_time.tv_sec, sent_time.tv_usec, (delay.tv_sec + (delay.tv_usec * 1e-6)));
	fprintf(fp, "%09u, %11zu, %11ld.%.6ld, %11ld.%.6ld, %9.6f\n", seq, seq_count * PACKET_SIZE, recv_time.tv_sec, recv_time.tv_usec, sent_time.tv_sec, sent_time.tv_usec, (delay.tv_sec + (delay.tv_usec * 1e-6)));
	
	gettimeofday(&cur_time, NULL);
	fprintf(fp, "END FLOW from %s:%s at TIME %ld.%.6ld, BYTES %zd\n", host, service, cur_time.tv_sec, cur_time.tv_usec, ntotal);
	fflush(fp);
      }
      
      if (verbose)
       	cout << proc_prefix << "Closing connection." << endl;
      
      close(sockfd_client);
      
      if (log)
	fclose(fp);
      
      return 0;
    }
    
    if (verbose)
      cout << proc_prefix << "Forked child process " << pid << " to handle the connection." << endl;
    
    close(sockfd_client);
    
  } // end while loop

  // wait for children to finish
  if (verbose)
    cout << proc_prefix << "Waiting for any children to terminate ..." << endl;
  pid_t pid;
  int stat;
  while ( (pid = waitpid(-1, &stat, 0)) > 0 )
    if (verbose)
      cout << proc_prefix << "Server child " << pid << " has terminated." << endl;
    
  if (verbose) 
    cout << proc_prefix << "Stopping the server ..." << endl;
  close(sockfd);
  
  if (verbose)
    cout << proc_prefix << "Finished the experiment." << endl;
  
  return 0;
}
