// call_perf.c
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <fcntl.h>
#include <assert.h>
#include <sys/types.h>
#include <dirent.h>
#include "misc.h"
#include "SS7Decoder.h"
#include "LogAPI.h"
#include "MapLoad.h"
//#include "MSdebugMsg.H"
//#include "MSregister.H"
#include "TRflags.H"

#include "GIQueueStation.H"
#include "GIQueueDef.H"

#include <pthread.h>
//#include "genInc/APmapv1OperationFactory.H"
//#include "genInc/APmapv2OperationFactory.H"
//#include "genInc/APmapv3OperationFactory.H"

using namespace std;

int period_time_is_out = 0;

unsigned long long summy_tranfer_rate = 0; 
unsigned long long summy_period_time = 0;
unsigned long long summy_call_times = 0;

time_t g_start_time = 0;
unsigned long long g_send_interval = 0;

static const char *MSG_QUE = "MSGQUE";

void do_alarm(int sig);
void do_exit();

int usage(char *prog)
{
	printf("%s [-r tranfer_rate] [-t period_time] [-n call_times] [-m thread_number] -f input_file\n", prog);
	return 0;
}

void *consumer(void *p)
{
	GIqid msgQ;
	char msg_buf[20480];
	int msgsz = 0;
	bool ret = false;
	const string ProtocolType = "map";
	string jsonStr;

	bool debug_mode = *((bool *)p);

	GIQueueStation::getInstance()->getQbyName(msgQ, "MSGQUE");
	while (1)
	{
		memset(msg_buf, 0, sizeof(msg_buf));
		msgsz = 0;
		GIQueueStation::getInstance()->receive(msgQ, msg_buf, msgsz, 100000);
		if (msgsz > 0)
		{
			char output_file_name[128] = {0};
			unsigned char data_buffer_str[1024] = {0};

			int raw_data_len = msgsz -  128;

			memcpy(output_file_name, msg_buf, 128);
			memcpy(data_buffer_str, msg_buf + 128, raw_data_len);

			string rawData;
			for (int i = 0; i < raw_data_len; i++)
			{
				rawData += data_buffer_str[i];
			}

			if ((ret = SS7DECODER::SS7Decoder(rawData, ProtocolType, "ITU", jsonStr)) == false)
			{
				fprintf(stderr, "decode data error\n");
			} 
			else
			{
				//printf("jsonStr = %s\n", jsonStr.c_str());
			}

			if (debug_mode)
			{
				int fd = open(output_file_name, O_CREAT|O_WRONLY, S_IRUSR|S_IWUSR|S_IRGRP|S_IWGRP);
				write(fd, jsonStr.c_str(), jsonStr.length());
				close(fd);
			}
		}
	}
}

void *producer(unsigned long long ct, unsigned long long period_time, unsigned long long tranfer_rate)
{
	DIR *dp = NULL;
	struct dirent *dirp = NULL;
	GIqid msgQ;

	// timer expiring will update period_time_is_out
	signal(SIGALRM, do_alarm);
	alarm(period_time);

	GIQueueStation::getInstance()->getQbyName(msgQ, "MSGQUE");

	while (1)
	{
		// open file to get data
		if( (dp = opendir( "." )) == NULL )
		{
		}
		while( ct && !period_time_is_out && ( dirp = readdir( dp ) ) != NULL) 
		{  
			if(strcmp(dirp->d_name,".")==0  || strcmp(dirp->d_name,"..")==0)  
			{
				continue;  
			}

			int size = strlen(dirp->d_name);  

			if(size < 5)     
			{
				continue;  
			}

			if(strcmp( ( dirp->d_name + (size - 4) ) , ".raw") != 0)  
			{
				continue;  
			}

			printf("file name: %s\n", dirp->d_name);

			int infd = -1;
			if ((infd = open(dirp->d_name, O_RDONLY)) < 0)
			{
				continue;
			}

			char output_file_name[128] = {0};
			snprintf(output_file_name, 128, "%s.json", dirp->d_name);

			int nread = 0;
			unsigned char data_buffer_str[1024] = {0};
			unsigned char data_buffer_str_with_operation_info[2048] = {0};
			nread = read(infd, data_buffer_str, sizeof(data_buffer_str));
			if (nread < 0) 
			{
				continue;
			}

			memcpy(data_buffer_str_with_operation_info, output_file_name, 128);
			memcpy(data_buffer_str_with_operation_info + 128, data_buffer_str, nread);

			print_buf2(data_buffer_str, nread, 0);
			int rtn = GIQueueStation::getInstance()->send(msgQ, (const char*)data_buffer_str_with_operation_info, nread + 128);
			if (rtn)
			{
				continue;
			}

			// send interval in order to produce the message averagely
			if (tranfer_rate != 0) 
			{
				g_send_interval = 1000000/tranfer_rate;
			}
			else
			{
				g_send_interval = 0;
			}
			usleep(g_send_interval);


			// call time decrease and total call time increase
			ct--;
			summy_call_times++; 

			close(infd);
		}
		closedir(dp);
	}
}

int main(int argc, char **argv)
{
	unsigned long long tranfer_rate = 0xffffffffffffffff; // default: no control
	unsigned long long period_time = 0xffffffffffffffff;  // default: forever
	unsigned long long call_times = 0xffffffffffffffff;       // default: no control
	unsigned long long thread_number = 1;
	char input_file[1024] = "./buf.out.txt";
	bool debug_mode = false;

	//MSInit("ss7decoderapp");
	GIqid msgQ = (GIQueueStation::getInstance())->createQ( MSG_QUE, 20000);

	//load map libraries
	//mapv1_load();
	//mapv2_load();
	//mapv3_load();

        SS7DECODER::map_load();

	int ch = 0; 
	printf("optind = %d, argc = %d\n", optind, argc);

	while ((ch = getopt(argc,argv,"dr:t:n:m:f:"))!=-1)  
	{  
		switch(ch)  
		{  
			case 'r':  
				tranfer_rate = (unsigned long long)atol(optarg); 
				break;  
			case 't':  
				period_time = (unsigned long long)atol(optarg);
				break;  
			case 'n':  
				call_times = (unsigned long long)atol(optarg);
				break;  	
			case 'm':  
				thread_number = (unsigned long long)atol(optarg);
				break;  							
			case 'f':  
				strncpy(input_file, optarg, sizeof(input_file));    
				break; 
			case 'd':
				debug_mode = true;
				break;
			default:  
				usage(argv[0]);  
		}  
	}

	printf("Params:\n");
	printf("  tranfer_rate:%llu\n", tranfer_rate);
	printf("  period_time:%llu\n", period_time);
	printf("  call_times:%llu\n", call_times);
	printf("  thread_number:%llu\n", thread_number);
	printf("  input_file:%s\n", input_file);
	printf("  debug_mode:%d\n", debug_mode);
#if 0
	// main initialization
	g_start_time = time(NULL);
#endif

	//create three working threads pull the messages from the queue
	pthread_t t1, t2, t3, tid;
	pthread_create(&t1, NULL, consumer, (void *)(&debug_mode)); 
	pthread_create(&t2, NULL, consumer, (void *)(&debug_mode)); 
	pthread_create(&t3, NULL, consumer, (void *)(&debug_mode)); 

	tid = pthread_self();
	if ( (tid != t1) && (tid != t2) && (tid != t3))
	{
		producer(call_times, period_time, tranfer_rate);
	}

	pthread_join(t1, NULL);
	pthread_join(t2, NULL);
	pthread_join(t3, NULL);

	do_exit();
	return 0;
}

void do_alarm(int sig)
{
	printf("Time out, will do exit...\n");
	period_time_is_out = 1;

	return;
}

void do_exit()
{

	summy_period_time = time(NULL) - g_start_time;
	if (summy_period_time)
		summy_tranfer_rate = summy_call_times/summy_period_time;
	else 
		summy_tranfer_rate = 0;

	printf("Summy:\n");
	printf("  summy_period_time:%llu", summy_period_time);
	if (!summy_period_time) printf(" (less than 1 second)");
	printf("\n");
	printf("  summy_call_times:%llu\n", summy_call_times);
	printf("  summy_tranfer_rate:%llu\n", summy_tranfer_rate);

	return;
}

