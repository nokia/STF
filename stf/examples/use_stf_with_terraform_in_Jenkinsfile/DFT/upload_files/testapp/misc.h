

#ifndef _MISC_H
#define _MISC_H
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>




struct split_var {
	void *addr;
	int maxlen;
};

typedef int(*split_fp)(char *str, void *addr, int maxlen);

int str_bin2asc(unsigned char *bin_str, int bs_len, char *asc_str, int as_maxlen);

int sf_s2i(char *str, void *addr, int maxlen);
int sf_scp(char *str, void *addr, int maxlen);
int sf_s2ul(char *str, void *addr, int maxlen);
int sf_s2us(char *str, void *addr, int maxlen);
int str_split(char *orig_str, int delim, split_fp func, struct split_var split_var_table[], int split_var_max);

int getvarbydeli(char *begin,char *end,char *fdeli,int flen,char *ldeli,int llen,char *var,int maxvarlen);
void print_var(char *varname, char *var, int len);

void print_buf(unsigned char *buf, int nbuf, unsigned int column);
void print_buf2(unsigned char *buf, int nbuf, unsigned int column);

char *new_strchr(char *string, char *delim);
char *mem_find(char *mem_mother, char *mem_son, int mother_len, int son_len);

char *search_sense_char(char *begin, int nsearch, int step);
char *search_nosense_char(char *begin, int nsearch, int step);
int char2num(char p);
char num2char(int p);
int asc2hex(char *src, int slen, unsigned char *dst, int dmaxlen);
int hex2asc(unsigned char *src, int slen, char *dst, int dmaxlen);


extern inline void rest(void);


#define UINT_GT(x,y)     ((y) - (x) > 0x7fffffff)
#define UINT_LT(x,y)     ((x) - (y) > 0x7fffffff)
#define UINT_EQ(x,y)     ((x) == (y))
#define UINT_GE(x,y)     ((x) - (y) < 0x7fffffff)
#define UINT_LE(x,y)     ((y) - (x) < 0x7fffffff)


#ifndef MIN
#define MIN(a, b)	((a) > (b) ? (b) : (a))
#endif 

#ifndef MAX
#define MAX(a, b)	((a) > (b) ? (a) : (b))
#endif 

#ifdef DEBUG_DUMP
#define DUMP(...) \
	do {\
		N_PRINTF("DUMP >> ");\
		N_PRINTF(__VA_ARGS__);\
		N_PRINTF("\n");\
	} while(0)
#else
#define DUMP(...) \
	do {\
	} while(0)
#endif

#ifdef DEBUG_DUMP_ERR
#define DUMP_ERR(...) \
	do {\
		N_FPRINTF(stderr, "** DUMP ERROR <in %s line %d> >> ", __FILE__, __LINE__);\
		N_FPRINTF(stderr, __VA_ARGS__);\
		N_FPRINTF(stderr, "\n");\
	} while(0)
#else
#define DUMP_ERR(...) \
	do {\
	} while(0)
#endif

#ifdef DEBUG_DUMP
#define DUMP_R(...) \
	do {\
		N_PRINTF(__VA_ARGS__);\
	} while(0)
#else
#define DUMP_R(...) \
	do {\
	} while(0)
#endif



#ifdef CLOSURE_MODE
#define N_PRINTF(...) \
	do {\
	} while(0)

#define N_FPRINTF(...) \
	do {\
	} while(0)

#define snN_PRINTF(...) \
	do {\
		snprintf(__VA_ARGS__); \
	} while(0)


#define fN_PRINTF(...) \
	do {\
	} while(0)

#else

#define N_PRINTF(...) \
	do {\
		printf(__VA_ARGS__); \
	} while(0)

#define N_FPRINTF(...) \
	do {\
		fprintf(__VA_ARGS__); \
	} while(0)

#define snN_PRINTF(...) \
	do {\
		snprintf(__VA_ARGS__); \
	} while(0)

#define fN_PRINTF(...) \
	do {\
		fprintf(__VA_ARGS__); \
	} while(0)

#endif

#ifndef offset_of
#define offset_of(str, member)  ((char *)(&((str *)0)->member) - (char *)0)
#endif

#endif 

