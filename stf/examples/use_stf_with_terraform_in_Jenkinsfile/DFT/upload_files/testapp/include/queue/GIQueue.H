#ifndef _GIQUEUE_H
#define _GIQUEUE_H

/*
 * This GIQueue class defines the basic functionalities of the FIFO queue, 
 * which including sending/receiving a message, statistics, conditional 
 * blocking, etc.
 */
#include <pthread.h>
#include <queue>
#include <stdlib.h>
#include <string.h>
#include "GIQueueDef.H"
#include "GIQMsgBase.H"

class GIQueue {

  public:
    GIQueue( unsigned int highWaterMark = GIQ_HIGH_WATER_MARK_DEFAULT );
    ~GIQueue(); 

    int send( const char *msgBuf, int msgSize );
    int receive( char *msgBuf, int &msgSize, int msTimerToWait = 0 );
    int getStats( GIqStats &stats, bool resetFlag = true );
    void setWaterMark( unsigned int highWaterMark );

  private:
    class GIqInternalMsg {
      public:
        GIqInternalMsg( const char *msg, int sz ) {
            if ( sz <= 0 ) {
                buf = 0; len = 0;
                return; 
            }
            if ( msg ) {
                buf = (char*)malloc(sz); len = sz;
                if(buf)
                {
                	memcpy(buf, msg, len);
                }else
                {
                	buf = 0; len = 0;
                }

            } else {
                buf = 0; len = 0;
            }
        }
        ~GIqInternalMsg() {
            if ( buf ) free(buf);
            buf = 0; len = 0;
        }

      public:
        char *buf;
        int len;
    };
 
  private:
    void resetStats();

  private:
    std::queue< GIqInternalMsg * > pq;     // queue for GIQMsgBase
    GIqStats qStats;               // measurement data for the queue

    unsigned int waterMark;       // limit number of msgs in queue
    unsigned int ctrlWaterMark;   // local control watermark for handling prio calls

    pthread_cond_t  cond;   // condition variable
    pthread_mutex_t  mtx;   // Mutex and conditional variable to protect 
    int eventFlag;          // the flag for cond
};

#endif
