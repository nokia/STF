#include <sys/types.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <stdarg.h>
#include <string.h>
#include <sched.h>
#include "misc.h"

static unsigned char transtbl_i2a[17] = "0123456789ABCDEF";
/*
 * str_bin2asc
 * example: 0x12345678 --> "12 34 56 78\0"
 * so if want change all binary string of X Bytes, the length of 
 * ascii string must be 3*XBytes
 */
int str_bin2asc(unsigned char *bin_str, int bs_len, char *asc_str, int as_maxlen)
{
	int as_len = 0;
	int real_bs_len = 0;
	int i;
	unsigned char low, high;

	if (!bin_str || !asc_str)
		goto err;

	real_bs_len = as_maxlen/3 > bs_len ? bs_len : as_maxlen/3;

	for (i = 0; i < real_bs_len; i++) {
		high = bin_str[i] >> 4;
		low  = bin_str[i] & 0xf;
	
		asc_str[as_len++] = transtbl_i2a[high];
		asc_str[as_len++] = transtbl_i2a[low];
		asc_str[as_len++] = ' ';
	}
	if (as_len) {
		as_len--;
		asc_str[as_len] = '\0';
	}
	
	return as_len;
err:
	return -1;
}

#if 0
/* 
 */
int DUMP(const char *format, ...)
{
#ifdef DEBUG_DUMP
	va_list ap;
	int ret;

	va_start(ap, format);
	ret = vprintf(format, ap);
	va_end(ap);

	return ret;
#else
	return 0;
#endif
}


/*
 * -1 failed, >= 0  ok.
 */
inline int get_first_str(char *begin, char *end, char *buff, int bufflen)
{
	int count;


	if (begin >= end) return -1;

	for (count = 0; (begin + count < end && count < bufflen); count++) {
		if (isspace(*(begin + count))) {
			if (count != 0) {
				strncpy(buff, begin, count);
				buff[count] = 0;
			}

			return count;
		}
	}

	if (begin + count == end) {
		
		if (count != 0) {
			strncpy(buff, begin, count);
			buff[count] = 0;
		}

		return count;
	}

	return -1;
}

#endif

#if 0
main(int argc, char **argv)
{
	char asc_str[96];
	char bin_str[32];
	int bin_str_sz;
	int i;
	int len;

	bin_str_sz = sizeof(bin_str);
	for (i = 0; i < bin_str_sz; i++)
	{
		bin_str[i] = i;
	}
	len = str_bin2asc(bin_str, sizeof(bin_str), asc_str, sizeof(asc_str));
	assert(len == strlen(asc_str));
	N_PRINTF("len(%d) str(%s)\n", len, asc_str);

	return 0;
}
#endif


/*This function get var between two deli
	0: failed
   	>1:successed
	begin: 	databuffer's begin
	end :  	databuffer's end
	fdeli: 	begin's Deli
	flen:  	begin's Deli length
	ldeli:  last's Deli
	llen:   last'Deli length
	var : 	the return var
	varlen:	var's length;

*/   
int getvarbydeli(char *begin,char *end,char *fdeli,int flen,char *ldeli,int llen,
		char *var,int maxvarlen)
{
	int varlen;
	char *index ;
	char *fvar = 0;
	char *lvar = 0;
	/*from begin to end */
	for( index = begin; index < end; index++ ) {
		if(flen == 1) {
			if(*index == *fdeli) {
				fvar = index + 1;
				break;
			} else {
				continue;
			}
		}
	}
	if(!fvar) return 0;

	/*from end to begin */
	index = end-1;
	while( index > begin ) {
		if(llen == 1) {
			if(*index == *ldeli) {
				lvar = index;
				break;
			} else {
				index--;
				continue;
			}

		}	
	}
	if(!lvar) return 0;
	varlen = lvar - fvar;	
	if (varlen >= maxvarlen) {
		return 0;
	}
	strncpy(var,fvar,varlen);
	var[varlen] = '\0';
#ifdef	DEBUG_DUMP
	N_PRINTF("%s",var);
#endif
	return 1;

}
#if 0
/*
 *
 * CSC for process pop3 and smtp
 * Packet like this:
 * Command + SP + Command paras + CTL/LN
 */ 

void get_cmd(Packet_t *packet, char **cmd, int *pcmd_len, char **cmd_para, int *pcmd_para_len)
{
	char *index, *begin, *end;
	int i = 0;

	*pcmd_len = 0;
	*pcmd_para_len = 0;	
	assert(packet);
	index = begin = packet->tcp_payload;
	end = begin + packet->tcp_payload_len;
	*cmd = begin;
	while(index < end) {
		i++;
		if(*index == 0x20) {
			*cmd_para = index + 1;
			break;
		}
		if(*index == 0x0d) {
			*pcmd_len = i - 1;
			*pcmd_para_len = 0;
			return;
		}
		index++;
	}
	*pcmd_len = i - 1;
	i = 0;
	index++;
	while(index < end) {
		i++;
		if(*index == 0x0d) 
			break;
		index++;	
	}
	*pcmd_para_len = i - 1;
	/*
	DUMP_R("Para cmd len [%d] \n", *pcmd_len);
	if(*pcmd_len > 0) {
		for(i = 0; i < *pcmd_len; i++) {
			DUMP_R("%c", *(cmd + i));
		}
	}
	DUMP_R("\n");	
	DUMP_R("Para cmd param len [%d] \n", *pcmd_para_len);
	if(*pcmd_para_len > 0) {
		for(i = 0; i < *pcmd_para_len; i++) {
			DUMP("%c", *(cmd_para + i));
		}
	}	
	DUMP_R("\n");	
	*/
		
	return;	
}

#endif
void print_var(char *varname, char *var, int len)
{
	int i = 0;
	N_PRINTF("\n------------------------------\n");
	N_PRINTF(" %s: \n", varname);
	for(i = 0; i < len; i++) {
		N_PRINTF("%c", *(var + i));
	}
	N_PRINTF("\n-------------------------------\n");
}		
	

//
// split funcs
// return: n >= 0, result len in "addr", n < 0, error
// sf_s2i: convert string to int
int sf_s2i(char *str, void *addr, int maxlen)
{
	int n = 0;

	if (!addr || maxlen < 4)
		goto err;

	if (!str)
		*(int *)addr = 0;
	else
		*(int *)addr = atoi(str);

	n = sizeof(int);

	return n;
err:
	return -1;
}

int sf_scp(char *str, void *addr, int maxlen)
{
	if (!addr || maxlen < 1)
        return -1;

	if (!str) {
		*(char *)addr = 0;
        return 0;
	}

	if (strlen(str)+1 > maxlen) {
		*(char *)addr = 0;
        return 0;
	}
    char* addr_pointer = (char*)addr;
    strncpy(addr_pointer, str, maxlen);
    addr_pointer[maxlen - 1] = '\0';
}

//
// split a string to n part, every part will be a param to 'func', and fill the result
// to the address stored in struct split_var 's addr.
// if 'func' == NULL, call string copy(sf_scp) as default func
int str_split(char *orig_str, int delim, split_fp func, struct split_var split_var_table[], int split_var_max)
{
	char *tbuf = NULL;
	char *head = NULL, *tail = NULL;
	int nvar = 0;
	char *p = NULL;
	split_fp callfunc = NULL;

	if (!orig_str || !orig_str[0]) {
        return -1;
	}
    size_t s_size = strlen(orig_str) + 1;
    tbuf = (char *)malloc(s_size);
	if (!tbuf)
        return -1;

    strncpy(tbuf, orig_str, s_size);
    tbuf[s_size -1] = '\0';

	tail = tbuf;
	while (1) {
		if (!tail)
			break;

		head = tail;
		p = strchr(tail, delim);
		if (p) {
			*p = '\0';
			tail = p+1;
		} else
			tail = NULL;
		
		if (func)
			callfunc = func;
		else
			callfunc = sf_scp; /* default: string copy */

		if (callfunc(head, split_var_table[nvar].addr, split_var_table[nvar].maxlen) < 0) {
			N_FPRINTF(stderr, "Error: splited data convert error(%s)\n", head);
			continue;
		}

		nvar++;
		if (nvar == split_var_max)
			break;
	}

	free(tbuf);
	return nvar;
}

#if 0
int main(int argc, char **argv)
{
	int var1, var2;
	struct split_var var_table[5];
	int nsplit;

	var_table[0].addr = &var1;
	var_table[0].maxlen = sizeof(var1);

	var_table[1].addr = &var2;
	var_table[1].maxlen = sizeof(var2);

	nsplit = str_split(argv[1], ',', sf_s2i, var_table, 2);
	N_PRINTF("nsplit:%d, var1:%d, var2:%d\n", nsplit, var1, var2);

	return 0;
}

#endif

void print_buf(unsigned char *buf, int nbuf, unsigned int column)
{
	int i;
	int col;

	if (column == 0)
		col = 30;
	else
		col = column;

//	N_PRINTF("PrintBuf:Len:%d\n", nbuf);
	for (i = 0; i < nbuf; i++) {
		N_PRINTF("%x%x ", buf[i]>>4, buf[i]&0x0f);
		if ((i+1) % col == 0)
			N_PRINTF("\n");
	}
	N_PRINTF("\n");

	return;
}

void print_buf2(unsigned char *buf, int nbuf, unsigned int column)
{
	int i, j;
	int col;
	unsigned char ch;

	if (column == 0)
		col = 16;
	else
		col = column;

//	N_PRINTF("PrintBuf:Len:%d\n", nbuf);
	for (i = 0; i < nbuf; i++) {
		printf("%x%x ", buf[i] >> 4, buf[i] & 0xf);
		if ((i + 1) % col == 0) {
			for (j = 0; j < col; j++) {
				ch = *(buf + i + j - (col-1));
				printf("%c", isprint (ch) ? ch : '.');
			}
			printf("\n");
		}
	}
	for (j = 0; j < col - i % col; j++)
		printf("   ");
	for (j = 0; j < i % col; j++) {
		ch = *(buf + i + j - i % col);
		printf("%c", isprint (ch) ? ch : '.');
	}
	printf("\n");

	return;
}

#if 0
int main(int argc, char **argv)
{
	char *addr = NULL;
	int len;

	if (argc == 2)
		len = atoi(argv[1]);
	else
		len = 400;

	addr = malloc(len);

	print_buf(addr, len, 0);

	print_buf2(addr, len, 0);

	free(addr);

	return 0;
}
#endif

//
// new_strchr
// search any char in 'delim' which is first ocurr in 'string'
char *new_strchr(char *string, char *delim)
{
        int str_i;

        if (string == NULL || delim == NULL)
                return NULL;

        for (str_i = 0; str_i < strlen(string); str_i++) {
                char *p;

                p = strchr(delim, string[str_i]);  // find char in delimiters
                if (p != NULL) {
                        break;
                }
        }

        if (str_i == strlen(string)) {
                return NULL;
        } else
                return string+str_i;

}
char *mem_find(char *mem_mother, char *mem_son, int mother_len, int son_len){
	int i;
	if(mem_mother == NULL||mem_son == NULL||mem_son == 0||son_len == 0){
		return NULL;
	}
	for(i=0;i<mother_len-son_len;i++){
		if(memcmp(mem_mother+i,mem_son,son_len) == 0){
			return mem_mother+i;
		}
	}
	return NULL;
}

/* 
 * 找出三个指针中的最小一个非空指针
 */
unsigned min_p(unsigned long a, unsigned long b, unsigned long c)
{
	unsigned long min;

	min = (a-1)<(b-1)?(a-1):(b-1);
	if (c - 1 < min)
		min = c - 1;
	return min + 1;
}

/* 
 */
void rest(void)
{
#ifdef GPACK_USLEEP
			/* equal usleep(1 / HZ * 1000000) */;
			usleep(1);
#else
			sched_yield(); /* is better */
#endif
}

// search_nosense_char
// 寻找无意义的字符，这些字符是指' ', '\t', '\n', '\r'和0字符
// NULL: not found
// step: >=0 = forward search
// 	<0 = backward search
// 
char *search_nosense_char(char *begin, int nsearch, int step)
{
	char *p;
	char *pret = NULL;
	int i;

	p = begin;
	for (i = 0; i < nsearch; i++) {
		if (*p == 0 || *p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') {
			pret = p;
			goto ret;
		}

		if (step >= 0)
			p++;
		else 
			p--;
	}

ret:
	return pret;
}

// search_sense_char
// 寻找有意义的字符，这些字符是指除了' ', '\t', '\n', '\r'和0之外的字符
// NULL: not found
// step: >=0 = forward search
// 	<0 = backward search
// 
char *search_sense_char(char *begin, int nsearch, int step)
{
	char *p;
	char *pret = NULL;
	int i;

	p = begin;
	for (i = 0; i < nsearch; i++) {
		if (*p != 0 && *p != ' ' && *p != '\t' && *p != '\n' && *p != '\r') {
			pret = p;
			goto ret;
		}

		if (step >= 0)
			p++;
		else 
			p--;
	}

ret:
	return pret;
}

/*
 *
 */
int char2num(char p)
{
	int ret;

	if ((p >= '0') && (p <= '9'))	
		ret = p - '0';
	else if ((p >= 'a') && (p <= 'f'))	
		ret = p - 'a' + 10;
	else if ((p >= 'A') && (p <= 'F'))
		ret = p - 'A' + 10;	
	else
		ret = p;

	return ret;
}

char num2char(int p)
{
	int ret;

	if ((p >= 0) && (p <= 9)) {
		ret = p + '0';
	} else if ((p >= 10) && (p <= 15)) {
		ret = p - 10 + 'a';
	} else
		ret = 0;

	return ret;
}

/*
 *
 */
int asc2hex(char *src, int slen, unsigned char *dst, int dmaxlen)
{
	char *p;
	int cnt = 0;

	p = src;
	while(slen > 0 && cnt < dmaxlen)
	{
		dst[cnt] = (char2num(p[0]) * 16 + char2num(p[1]));
		slen -= 2;
		cnt++;
		p = p + 2;
	}

	return cnt;
}


/*
 *
 */
int hex2asc(unsigned char *src, int slen, char *dst, int dmaxlen)
{
	int dlen = 0;
	int si = 0;

	for (si = 0; si < slen && dlen < dmaxlen-1; si++) {
		int high = src[si]>>4;
		int low = src[si] & 0xf;

		dst[dlen] = num2char(high);
		dst[dlen+1] = num2char(low);

		dlen += 2;
	}

	return dlen;
}

