#!/usr/bin/python
# -*- coding: UTF-8 -*-
import random
import os
import struct
import sys

if __name__ == '__main__':

    # read input file
    os.chdir(".")
    for item in os.listdir('.'):
      if os.path.isfile(item) and item.endswith('.msg'):
        file = open(item,'r')
        content = [x.rstrip("\n") for x in file]
        file.close()
 
        data = [x.split() for x in content]
        buf = []
        for each in data:
    	    if len(each) >= 3 and len(each[0]) == 4 and each[0][0] >= '0' and each[0][0] <= '9':

                hex = int(each[2],16)
    		buf.append(hex)
 
        # write output file
        outfile = item + '.raw'
        outtxt = open(outfile, 'wb+')
        for byte in buf:
            outtxt.write(struct.pack('B',byte))
        outtxt.close()
