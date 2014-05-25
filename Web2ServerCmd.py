#!/usr/bin/env python 
from CCommunicator import CCommunicator
import cgi, cgitb
#import socket 
print "Content-Type: text/html\n"     # HTML is following
cgitb.enable()
import sys
raw_data = sys.stdin.read();
import re
reCmd = re.compile('cmd=(.*)', re.I)
cmd = re.match(reCmd, raw_data)
form = cgi.FieldStorage(keep_blank_values=True)


print raw_data

import time
timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
webid   = 'webid'+timestamp
suitename= 'suite'+timestamp
if cmd :
    cmd = cmd.group(1)
else:
    cmd = form.getvalue('cmd')
web =CCommunicator('webclient')
rsp =web.TxWEB2SERVER_CONTROL_COMMAND_UPDATE(webid, suitename,cmd)

import sys
if type(rsp)!=type(None):
    if len(rsp):  
        sys.stdout.write(rsp)
        sys.stdout.flush()
    else:
        #sys.stdout.write('\n')
        sys.stdout.flush()
else:
    sys.stdout.flush()
#exit()
