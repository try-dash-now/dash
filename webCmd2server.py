#!/usr/bin/env python 
from CCommunicator import CCommunicator
import cgi, cgitb
#import socket 
cgitb.enable()
import sys,cStringIO

copyInput = cStringIO.StringIO(sys.stdin.read())
form = cgi.FieldStorage(copyInput)
raw_data = copyInput.getvalue()

#raw_data ='''a&COMMAND=set%20caseresult%20end&EXPECT'''


import re
reCmd = re.compile('.+&COMMAND=(.*)&EXPECT', re.I)

#form = cgi.FieldStorage()
cmd = re.match(reCmd, raw_data)

print "Content-Type: text/html\n"     # HTML is following
#print                               # blank line, end of headers


def Cmd2CSVstring(cmd):
    import StringIO, csv
    line = StringIO.StringIO()
    w = csv.writer(line)
    w.writerow(cmd)
    return line.getvalue()

if cmd :
    cmd = cmd.group(1)
    cmd = str(cmd).replace('''%20''', ' ')
else:
    cmd = form.getvalue('COMMAND')
#print cmd
#print form
#print raw_data, cmd

web =CCommunicator('webclient')
#try:    
if form.getvalue("SUTNAME") !=None :
    #print 'cmd(%s)'%form.getvalue('COMMAND')
    rsp = web.TxWEB2SERVER_COMMAND_UPDATE(
                                          form.getvalue('WEBSESSIONID'), 
                                          form.getvalue('CASENAME'),
                                          cmd,#form.getvalue('COMMAND'),
                                          form.getvalue('EXPECT'),
                                          form.getvalue('WAITTIME'),
                                          form.getvalue("SUTNAME")
                                          )
    
    sutname = form.getvalue("SUTNAME")                                    
    cmd = cmd #form.getvalue('COMMAND')
    exp = form.getvalue('EXPECT')
    wt =  str(form.getvalue('WAITTIME')) 
    rsp = [sutname, cmd, exp,wt ]
    rsp ='\t|\t'.join(rsp)+'\n'
    #rsp=Cmd2CSVstring(rsp)
else:
    rsp = web.TxWEB2SERVER_COMMAND_UPDATE(
                                          form.getvalue('WEBSESSIONID'), 
                                          form.getvalue('CASENAME'),
                                          cmd ,#form.getvalue('COMMAND'),
                                          form.getvalue('EXPECT'),
                                          form.getvalue('WAITTIME')
                                          )
    #cmd=['SUT'  ,msg['SUTNAME'],  msg['COMMAND'], msg['EXPECT'], msg['WAITTIME']]
    #cmd=['CASE' ,None,           msg['COMMAND'], msg['EXPECT'], msg['WAITTIME']]
    cmd = cmd#form.getvalue('COMMAND')
    exp = form.getvalue('EXPECT')
    wt =  str(form.getvalue('WAITTIME')) 
    rsp = ['__CASE__', cmd, exp,wt ]
    rsp ='\t|\t'.join(rsp)+'\n'
    #rsp=Cmd2CSVstring(rsp)
#except Exception ,e :
#    print e
#    rsp=''
#print 'response is:',str(rsp)
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
