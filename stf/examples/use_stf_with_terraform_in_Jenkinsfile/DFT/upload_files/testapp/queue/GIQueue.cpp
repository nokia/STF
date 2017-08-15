#include <stdio.h>
#include "GIQueue.H"

// constructor
GIQueue::GIQueue( unsigned int highWaterMark )
{
	if ( highWaterMark > GIQ_HIGH_WATER_MARK_MAX ) {
		waterMark = GIQ_HIGH_WATER_MARK_MAX;
	} else {
		waterMark = highWaterMark;
	}

	// calculate the controlling highWaterMark value, 20% larger
	ctrlWaterMark = (unsigned int)( highWaterMark * 1.20 );

	// initialize the condition variable and mutex
	pthread_cond_init( &cond, NULL );
	pthread_mutex_init( &mtx, NULL );
	eventFlag = 0;

	// reset Q stats
	resetStats();
	qStats.water_mark_limit = waterMark;
}

GIQueue::~GIQueue()
{
	pthread_cond_destroy( &cond );
	pthread_mutex_destroy( &mtx );
}

int GIQueue::send( const char *msgBuf, int msgSize )
{
	if ( !msgBuf || msgSize <= 0 ) {
		return GIQRTN_BAD_MESSAGE;
	}

	pthread_mutex_lock( &mtx );
	
	// clone msg
	GIqInternalMsg *qMsg = new GIqInternalMsg( msgBuf, msgSize );

	// put the message into the queue
	pq.push( qMsg );

	qStats.num_msg_in = pq.size();
	qStats.num_msg_total++;
	qStats.num_bytes_in += msgSize;
	qStats.num_bytes_total += msgSize;

	if ( pq.size() > qStats.num_msg_high )
		qStats.num_msg_high = pq.size();

	if ( qStats.num_bytes_in > qStats.num_bytes_high )
		qStats.num_bytes_high = qStats.num_bytes_in;

	// trigger the thread awaiting now
	eventFlag = 1;
	pthread_cond_signal( &cond );

	pthread_mutex_unlock( &mtx );
	return GIQRTN_SUCCESS;
}

	int
GIQueue::receive( char *msgBuf, int &msgSize, int ms )
{
	int rc = 0;
	struct timespec   ts;
	struct timeval    tp;

	if ( ( rc = gettimeofday(&tp, NULL) ) != 0 ) {
		return GIQRTN_INTERNAL_ERROR;
	}

	// Convert from timeval to timespec (ms timer)
	ts.tv_sec  = tp.tv_sec + ms/1000 + (tp.tv_usec+(ms%1000)*1000)/1000000;
	ts.tv_nsec = ((tp.tv_usec + (ms%1000)*1000)%1000000) * 1000;

	pthread_mutex_lock( &mtx );

	if ( pq.size() == 0 ) {
		// shall update this flag here?
		eventFlag = 0; 

		if ( ms == 0 ) {
			// no msg and do not wait
			pthread_mutex_unlock( &mtx );
			return GIQRTN_NONE_MESSAGE;
		} else if ( ms < 0 ) {
			// no msg and wait till event happen
			rc = pthread_cond_wait(&cond, &mtx);
		} else {
			rc = pthread_cond_timedwait(&cond, &mtx, &ts);

			if ( rc == ETIMEDOUT ) {
				if( pq.size() == 0 && eventFlag == false ) {
					pthread_mutex_unlock( &mtx );
					return GIQRTN_TIME_OUT;
				}
			} else if ( rc == EPERM ) { // failed to get mutex
				// less likely happen
				pthread_mutex_unlock( &mtx );
				return GIQRTN_INTERNAL_ERROR;
			} // else, to ahead
		}
	}

	if (pq.empty() != true) 
	{


		GIqInternalMsg *qMsg = pq.front();
		pq.pop();

		if ( qMsg ) {
			memcpy( msgBuf, qMsg->buf, qMsg->len );
			msgSize = qMsg->len;
			qStats.num_msg_in = pq.size();
			if ( qStats.num_bytes_in > 0 && qStats.num_bytes_in >= qMsg->len )
				qStats.num_bytes_in -= qMsg->len;
			delete qMsg; qMsg = 0;
		} else {
			pthread_mutex_unlock( &mtx );
			return GIQRTN_INTERNAL_ERROR;
		}
	}
	pthread_mutex_unlock( &mtx );
	return GIQRTN_SUCCESS;
}

	int
GIQueue::getStats( GIqStats &stats, bool resetFlag )
{
	pthread_mutex_lock( &mtx );
	stats = qStats;
	if ( resetFlag == true ) {
		resetStats();
	}
	pthread_mutex_unlock( &mtx );

	return GIQRTN_SUCCESS;
}

	void
GIQueue::setWaterMark( unsigned int highWaterMark )
{
	if ( highWaterMark > GIQ_HIGH_WATER_MARK_MAX ) {
		waterMark = GIQ_HIGH_WATER_MARK_MAX;
	} else {
		waterMark = highWaterMark;
	}

	// calculate the controlling highWaterMark value, 20% larger
	ctrlWaterMark = (unsigned int)( highWaterMark * 1.20 );
	qStats.water_mark_limit = highWaterMark;
}

void
GIQueue::resetStats() {
	qStats.num_msg_in      = 0;
	qStats.num_msg_high    = 0;
	qStats.num_msg_lost    = 0;
	qStats.num_msg_total   = 0;
	qStats.num_bytes_in    = 0;
	qStats.num_bytes_high  = 0;
	qStats.num_bytes_lost  = 0;
	qStats.num_bytes_total = 0;

	gettimeofday(&(qStats.timeStamp), NULL);
}
