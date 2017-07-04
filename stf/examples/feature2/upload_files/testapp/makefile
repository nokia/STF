# Author: Gemfield
# Date: 2016-12-29
# Version: 1.0

REL_PATH= /usr/lib64/CSF-SS7DECODER
CPP_FLAGS= -c -g -O2 -fPIC -Wno-deprecated -DCC -DLX -D_SVR4 -Wno-invalid-offsetof -Wno-non-template-friend -m64
INC_FLAGS= -I/usr/include/CSF-SS7DECODER -I./include/queue

CPP_FILES := $(wildcard *.C)
OBJ_FILES := $(notdir $(CPP_FILES:.C=.o))

#LIBS := -L. -lqueue -L$(REL_PATH)/lib -lss7Decoder -ltcap -lsccplayer -lmapv1 -lmapv2 -lmapv3 -lbase -lEDbase -lbedl -lmsdebug -lpthread
LIBS := -L. -lqueue $(REL_PATH)/libss7Decoder.a $(REL_PATH)/libmapv1.a $(REL_PATH)/libmapv2.a $(REL_PATH)/libmapv3.a $(REL_PATH)/libss7Base.a -lpthread


all:  libqueue ss7decoderapp

libqueue:
	cd queue; make all

ss7decoderapp: call_perf.o misc.o $(REL_PATH)/libss7Decoder.a $(REL_PATH)/libmapv1.a $(REL_PATH)/libmapv2.a $(REL_PATH)/libmapv3.a $(REL_PATH)/libss7Base.a libqueue.a
	g++ -g -o $@ call_perf.o misc.o $(LIBS)

%.o: %.c
	g++ $(INC_FLAGS) $(CPP_FLAGS) -o $@ $<
		
clean:
	cd queue; make clean
	rm -f *.o
	rm -f *.a
	rm -f *.so
	rm -f ss7decoderapp
