#include "channel.hpp"

using namespace std;

//#define PORT 4311

static int quit = 0;
static FILE *fp;
static int sockfd;

/* SIGINT handler: set quit to 1 for graceful termination */
void
handle_sigint(int signum) {
  quit = 1;
}


/* Subtract the ‘struct timeval’ values X and Y,
   storing the result in RESULT.
   Return 1 if the difference is negative, otherwise 0. */
int
timeval_subtract (struct timeval *result, struct timeval *x, struct timeval *y)
{
  /* Perform the carry for the later subtraction by updating y. */
  if (x->tv_usec < y->tv_usec) {
    int nsec = (y->tv_usec - x->tv_usec) / 1000000 + 1;
    y->tv_usec -= 1000000 * nsec;
    y->tv_sec += nsec;
  }
  if (x->tv_usec - y->tv_usec > 1000000) {
    int nsec = (x->tv_usec - y->tv_usec) / 1000000;
    y->tv_usec += 1000000 * nsec;
    y->tv_sec -= nsec;
  }

  /* Compute the time remaining to wait.
     tv_usec is certainly positive. */
  result->tv_sec = x->tv_sec - y->tv_sec;
  result->tv_usec = x->tv_usec - y->tv_usec;

  /* Return 1 if result is negative. */
  return x->tv_sec < y->tv_sec;
}


int main(int argc, char**argv)
{
  int PORT;
  float delay;
  int nrecv, nsend;
  struct sockaddr_in bind_addr;
  struct sockaddr_storage client_addr;
  socklen_t client_addr_len;
  // char serv_ip[256];
  int sockfd_client;

  struct timeval cur_time;
  char filename[256];
  bool verbose = false;
  
  packet_t pdu_data;
  
  const size_t PACKET_SIZE = sizeof(packet_t);
  
  if (argc != 4) {
    printf ("Usage: %s <port> <logfilename> <verbose>\n", argv[0]);
    exit(0);
  }

  // sprintf(serv_ip, "%s", argv[1]);
  PORT = atoi(argv[1]);
  sprintf(filename, "./%s", argv[2]);
  verbose = bool(atoi(argv[3]));
  
  // creating the remote struct for sending the packet initialization from the user side
  sockfd = socket(AF_INET, SOCK_STREAM, 0);

  int enable = 1;
  if ( (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof (enable)) != 0) ||
       (setsockopt(sockfd, SOL_SOCKET, SO_REUSEPORT, &enable, sizeof(enable)) != 0) ) {
    fprintf(stderr, "set sockopt failed [%s]\n", strerror(errno));
    exit(-1);
  }

  // bind the socket to the the port number
  memset(&bind_addr, 0, sizeof(bind_addr));
  bind_addr.sin_family = AF_INET;
  bind_addr.sin_addr.s_addr = INADDR_ANY;
  // bind_addr.sin_addr.s_addr = inet_addr(serv_ip);
  bind_addr.sin_port = htons(PORT);
  
  if (bind(sockfd, (struct sockaddr *)&bind_addr, sizeof(bind_addr)) < 0) {
    fprintf(stderr, "bind failed [%s]\n", strerror(errno));
    exit(-1);
  }
  
  fp = fopen(filename, "w");

  // set up interrupt handler for graceful termination
  struct sigaction sigact;
  sigact.sa_handler = handle_sigint;
  sigaction(SIGINT, &sigact, NULL);
  
  while ( !quit ) {
    
    // listen for connections
    listen(sockfd, 2);
    if (verbose)
      cout << "Listening for new connections ..." << endl;
    
    if ((sockfd_client = accept(sockfd, (struct sockaddr *) &client_addr, &client_addr_len)) < 0) {
      fprintf(stderr, "accept failed [%s]\n", strerror(errno));
      exit(-1);
    }
    
    char host[NI_MAXHOST], service[NI_MAXSERV];
    int s = getnameinfo((struct sockaddr *) &client_addr, client_addr_len, host, NI_MAXHOST, service, NI_MAXSERV, NI_NUMERICSERV);
    
    if (s == 0)
      if (verbose)
	printf("Accepted connection from %s:%s\n", host, service);
    else
      fprintf(stderr, "getnameinfo: [%s]\n", gai_strerror(s));

    // tcp flow started
    gettimeofday(&cur_time, NULL);
    fprintf(fp, "\nSTART FLOW %s:%s TIMESTAMP %ld.%3.6ld\n", host, service, cur_time.tv_sec, cur_time.tv_usec);
    fprintf(fp, "SEQ,\t received_time,\t sent_time,\t delay_s\n");
    
    // receive data from user
    while ((nrecv = recv(sockfd_client, &pdu_data, PACKET_SIZE, 0)) > 0) {
      gettimeofday(&cur_time,NULL);
      delay = (cur_time.tv_sec - pdu_data.seconds) + (cur_time.tv_usec - pdu_data.micros) / 1e6;
      fprintf(fp, "%3.9u,\t %ld.%3.6ld,\t %ld.%3.6ld,\t %f\n", pdu_data.seq, cur_time.tv_sec, cur_time.tv_usec, pdu_data.seconds, pdu_data.micros, delay);
    }

    // tcp flow ended
    gettimeofday(&cur_time, NULL);
    fprintf(fp, "END FLOW %s:%s TIMESTAMP %ld.%3.6ld\n", host, service, cur_time.tv_sec, cur_time.tv_usec);

    fflush(fp);

    if (verbose)
      cout << "Done receiving data, closing connection." << endl;
     
    close(sockfd_client);
  } // end while loop
  
  cout << "Stopping the server ..." << endl;
  close(sockfd);
  
  fclose(fp);

  cout << "Finished the experiment." << endl;
   
  return 0;
}
