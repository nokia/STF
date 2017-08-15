#include <pthread.h>
#include "GIQueueStation.H"

GIQueueStation* GIQueueStation::qStation = (GIQueueStation*)0;
pthread_mutex_t  GIQueueStation::mtx = PTHREAD_MUTEX_INITIALIZER;

GIQueueStation::GIQueueStation()
{
}

GIQueueStation::~GIQueueStation()
{
}

GIQueueStation*
GIQueueStation::getInstance() {
    if ( !qStation ) {
        pthread_mutex_lock( &mtx );
        if ( !qStation ) {
            qStation = new GIQueueStation();
        }
        pthread_mutex_unlock( &mtx );
    }

    return qStation;
}

void
GIQueueStation::destroyGIQueueStation(){

    pthread_mutex_lock( &mtx );
    if ( qStation ) {
        delete qStation;
    }
    pthread_mutex_unlock( &mtx );

}

GIqid
GIQueueStation::createQ( std::string name, unsigned int highWaterMark )
{
    GIqid qid = 0;

    int ret = getQbyName( qid, name );

    // check if name ever registered
    if ( ret == GIQRTN_SUCCESS ) {
        return qid;
    }

    pthread_mutex_lock( &mtx );
    GIQueue *q = new GIQueue( highWaterMark );
    qMap.insert( std::map<GIQueue*, std::string>::value_type( q, name ) );
    pthread_mutex_unlock( &mtx );

    return (GIqid)q;
}

int
GIQueueStation::removeQ( std::string name )
{
    GIqid qid = 0;
    int ret = getQbyName( qid, name );

    // check if name ever registered
    if ( ret != GIQRTN_SUCCESS ) {
        return ret;
    }

    pthread_mutex_lock( &mtx );
    qMap.erase( (GIQueue*)qid );
    pthread_mutex_unlock( &mtx );

    return GIQRTN_SUCCESS;
}

int
GIQueueStation::getQbyName( GIqid &qid, std::string name )
{
    pthread_mutex_lock( &mtx );

    std::map<GIQueue*,std::string>::iterator it;
    for ( it = qMap.begin(); it != qMap.end(); it++ ){
        if ( it->second.compare( name ) == 0 ) {
            qid = (GIqid)it->first;
            pthread_mutex_unlock( &mtx );
            return GIQRTN_SUCCESS;
        }
    }

    qid = 0;
    pthread_mutex_unlock( &mtx );
    return GIQRTN_QUEUE_NOT_FOUND;
}

int
GIQueueStation::send( GIqid toQid, const char *msgBuf, int msgSize )
{
    pthread_mutex_lock( &mtx );
    std::map<GIQueue*, std::string>::iterator it = qMap.find( (GIQueue*)toQid );
    if ( it == qMap.end() ) {
        pthread_mutex_unlock( &mtx );
        return GIQRTN_QUEUE_NOT_FOUND;
    }

    GIQueue* q = (GIQueue*) toQid;
    if( !q ){
        pthread_mutex_unlock( &mtx );
        return GIQRTN_QUEUE_NOT_FOUND;
    }
    pthread_mutex_unlock( &mtx );

    int ret = q->send( msgBuf, msgSize );
    return ret;
}

int
GIQueueStation::receive( GIqid fromQid, 
                         char *msgBuf, int &msgSize, int msTimerToWait )
{
    pthread_mutex_lock( &mtx );
    std::map<GIQueue*, std::string>::iterator it = qMap.find( (GIQueue*)fromQid );
    if ( it == qMap.end() ) {
        pthread_mutex_unlock( &mtx );
        return GIQRTN_QUEUE_NOT_FOUND;
    }
    pthread_mutex_unlock( &mtx );

    GIQueue* q = (GIQueue*) fromQid;
    int ret = q->receive( msgBuf, msgSize, msTimerToWait );
    
    return ret;
}

bool
GIQueueStation::ping( std::string name )
{
    GIqid qid = 0;
    int ret = getQbyName( qid, name );

    // check if name ever registered
    if ( ret == GIQRTN_SUCCESS ) {
        return true;
    } else {
        return false;
    }
}

int
GIQueueStation::getStats( GIqid qid, GIqStats &stats, bool resetFlag )
{
    pthread_mutex_lock( &mtx );
    std::map<GIQueue*, std::string>::iterator it = qMap.find( (GIQueue*)qid );
    if ( it == qMap.end() ) {
        pthread_mutex_unlock( &mtx );
        return GIQRTN_QUEUE_NOT_FOUND;
    }
    pthread_mutex_unlock( &mtx );

    GIQueue* q = (GIQueue*) qid;
    q->getStats( stats, resetFlag );

    return GIQRTN_SUCCESS;
}

int
GIQueueStation::updateQwaterMark( std::string name, unsigned int highWaterMark )
{
    GIqid qid = 0;
    int ret = getQbyName( qid, name );

    // check if name ever registered
    if ( ret != GIQRTN_SUCCESS ) {
        return ret;
    }

    GIQueue* q = (GIQueue*) qid;
    q->setWaterMark( highWaterMark );

    return GIQRTN_SUCCESS;
}

int
GIQueueStation::updateQwaterMark( GIqid qid, unsigned int highWaterMark )
{
    pthread_mutex_lock( &mtx );
    std::map<GIQueue*, std::string>::iterator it = qMap.find( (GIQueue*)qid );
    if ( it == qMap.end() ) {
        pthread_mutex_unlock( &mtx );
        return GIQRTN_QUEUE_NOT_FOUND;
    }
    pthread_mutex_unlock( &mtx );

    GIQueue* q = (GIQueue*) qid;
    q->setWaterMark( highWaterMark );

    return GIQRTN_SUCCESS;
}

std::string
GIQueueStation::nameOfQid( GIqid qid )
{
    std::string name;
    pthread_mutex_lock( &mtx );
    std::map<GIQueue*, std::string>::iterator it = qMap.find( (GIQueue*)qid );
    if ( it == qMap.end() ) {
        pthread_mutex_unlock( &mtx );
        name = "null";
        return name;
    }
    name = it->second;
    pthread_mutex_unlock( &mtx );

    return name;
}

/*
void
GIQueueStation::dump()
{
    pthread_mutex_lock( &mtx );
    std::map<GIQueue*, std::string>::iterator it;
    for ( it = qMap.begin(); it != qMap.end();it++ ){
        printf("elem in qMap: key=%s, val=%p\n",it->first.c_str(),it->second);
    }
    pthread_mutex_unlock( &mtx );
}*/
