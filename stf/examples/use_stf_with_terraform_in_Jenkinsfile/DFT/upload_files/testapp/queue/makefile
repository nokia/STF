REL_PATH= $(shell cd ../;pwd)
CPPFILES=$(wildcard *.cpp)
OBJS=$(patsubst %.cpp, %.o, $(notdir $(CPPFILES)))
SAMPLE=$(patsubst %.C, %.o, $(notdir $(wildcard *.C)))

CPPFLAGS=-g -fPIC -I$(REL_PATH)/include/queue

all : libqueue.a

libqueue.a : $(OBJS)
	ar -rcs $(REL_PATH)/$@ $^
	g++ -shared -o $(REL_PATH)/libqueue.so $^

%.o : %.cpp
	g++ $(CPPFLAGS) -c -o $@ $<

clean: 
	rm -f *.o
	rm -f $(REL_PATH)/libqueue.a
	rm -f $(REL_PATH)/libqueue.so
