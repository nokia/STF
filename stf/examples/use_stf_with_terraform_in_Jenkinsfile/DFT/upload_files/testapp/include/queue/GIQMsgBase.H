#ifndef _GIQMSGBASE_H
#define _GIQMSGBASE_H

/*
 * The class GIQMsgBase is the base class for messages which will
 * be transported through the internal GIQueue. All types of messages 
 * used in the queue should inherit from this base class.
 *
 */

const int GIQ_MAX_MSG_SIZE = 128*1024;

enum {
    GIQPriTypeClass1 = 0, // rejected when highWaterMark reached
    GIQPriTypeClass2 = 1, // accepted when highWaterMark < qSize < ctrlWaterMark 

    // maximum priority type
    GIQMaxPriType = 255
};

class GIQMsgBase {
public:
    GIQMsgBase(int messageType, unsigned char priorityType = GIQPriTypeClass1) {
        msgType = messageType; 
        priType = priorityType; 
    }
    virtual ~GIQMsgBase(){};

public:
    int  msgType;
    unsigned char priType;
};

#endif
