import sys
import datetime

msg_prefix = 'STF'
def errorAndExit(msg):
    print('%s Error! %s\n' %(msg_prefix, msg))
    sys.exit(1)

def note(msg):
    print("%s NOTE: %s ." %(msg_prefix, msg))

def warning(msg):
    print("%s Warning: %s ." % (msg_prefix, msg))

def getPidStatus(pid):
    try:
        for line in open("/proc/%d/status" % pid).readlines():
            if line.startswith("State:"):
                return line.split(":",1)[1].strip().split(' ')[0]
    finally:
        return 'N'

def second2date(second):
    return datetime.datetime.fromtimestamp(second).strftime('%Y-%m-%d %H:%M:%S')
