#ifndef _GIQUEUEDEF_H
#define _GIQUEUEDEF_H
#include <inttypes.h>
/*
 * This file defines some constants used for GIQueue and GIQueueStation.
 * The queue users should check and handle these constants properly.
 */

#include <errno.h>
#include <sys/time.h>

// water mark defines
const int GIQ_HIGH_WATER_MARK_MAX     = 20000;
const int GIQ_HIGH_WATER_MARK_DEFAULT = 8888;

// return values for GIQueue class
const int GIQRTN_SUCCESS  = 0;
const int GIQRTN_FAIL     = -1;
const int GIQRTN_BAD_MESSAGE     = GIQRTN_FAIL - 1;
const int GIQRTN_BUFFER_FULL     = GIQRTN_FAIL - 2;
const int GIQRTN_BUFFER_OVERFLOW = GIQRTN_FAIL - 3;
const int GIQRTN_INTERNAL_ERROR  = GIQRTN_FAIL - 4;
const int GIQRTN_TIME_OUT        = GIQRTN_FAIL - 5;
const int GIQRTN_NONE_MESSAGE    = GIQRTN_FAIL - 6;

// return values for GIQueueStation class
const int GIQRTN_QUEUE_NOT_FOUND  = GIQRTN_FAIL - 255;
const int GIQRTN_NAME_DUPLICATED  = GIQRTN_FAIL - 256;

// typedef GIqid as pointer
typedef uintptr_t GIqid;

// statistic items of GIQueue
typedef struct {
    unsigned int num_msg_in;       // number of msgs currently in queue
    unsigned int num_msg_lost;     // number of msgs lost
    unsigned int num_msg_high;     // number of msgs when traffic peak
    unsigned int num_msg_total;    // number of msgs totally rcvd
    unsigned int num_bytes_in;     // number of bytes currently in queue
    unsigned int num_bytes_lost;   // number of bytes lost
    unsigned int num_bytes_high;   // number of bytes when traffic peak
    unsigned int num_bytes_total;  // number of bytes totally rcvd
    unsigned int water_mark_limit; // the maximum number of messages allowed

    struct timeval timeStamp;      // the time stamp when begin statistics
} GIqStats;

#endif
