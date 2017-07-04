#ifndef _GIQUEUESTATION_H
#define _GIQUEUESTATION_H

/*
 * The GIQueueStation class is a sigleton helper class for the GIQueue users to
 * create, access and distroy a GIQueue(qid) through an unique name which provided
 * by users. This class also can be used to send a message via a qid.
 *
 */
#include <string>
#include <map>
#include "GIQueue.H"

class GIQueueStation {

public:
    // create an instance of GIQueue with an unique name
    // if duplicated name provided, the existing qid will be returned
    GIqid createQ( std::string name,
                   unsigned int highWaterMark = GIQ_HIGH_WATER_MARK_DEFAULT );

    // get the GIqid of GIQueue by name
    int getQbyName( GIqid &qid, std::string name );

    // get the Name of GIQueue by GIqid
    std::string nameOfQid( GIqid qid );

    // remove a GIQueue mapping by name
    // it is users responsibility to clear the mapping record
    int removeQ( std::string name );

    // to check if a GIQueue exist or not for a given name
    bool ping( std::string name );

    int getStats( GIqid qid, GIqStats &stats, bool resetFlag = true );

    // send a message to the toQid
    int send( GIqid toQid, const char *msgBuf, int msgSize );

    // receive a message from the fromQid
    int receive( GIqid fromQid, char *msgBuf, int &msgSize, int msTimerToWait = 0 );

    // update the max number of messages allowed in Q - by name
    int updateQwaterMark( std::string name, unsigned int highWaterMark );

    // update the max number of messages allowed in Q - by qid
    int updateQwaterMark( GIqid qid, unsigned int highWaterMark );

public:
    // get the sigleton instance of the GIQueueStation
    static GIQueueStation* getInstance();

    // destroy the instance of the GIQueueStation
    static void destroyGIQueueStation();

private:
    GIQueueStation();  // constructor
    ~GIQueueStation(); // destructor

private:
    std::map<GIQueue*, std::string> qMap; // a GIQueue per an unique name

    static GIQueueStation* qStation;
    static pthread_mutex_t mtx;
};

#endif
