#!/usr/bin/env python 
TYPE    =   ['NULL','COMMANDLIST','SUTNAMELIST', 'WEBSESSIONID' ,
             'CASENAME','SUTNAME','CASECOMMAND', 'SUTCOMMAND', 
             'SUTRAWDATA','SUTCOMMANDLIST', 'CASERAWDATA', 'CASEERROR',
             'COMMAND','EXPECT','WAITTIME',
             'CASERESULT','LOGPATH','EOF'
             ]
MSGTYPE =   ['NULL',
             'WEB2SERVER_SUTOUT_REQ',
             'SERVER2WEB_SUTOUT_RESP',
             'CASE2SERVER_SUTOUT_UPDATE',#'SERVER2CASE_SUTOUT_UPDATE_ACK',
             'WEB2SERVER_COMMAND_UPDATE',#'SERVER2WEB_COMMAND_ACK',
             #'WEB2SERVER_CASE_COMMAND_UPDATE',
             'CASE2SERVER_COMMAND_REQ',
             'SERVER2CASE_COMMAND_RESP',
             'WEB2SERVER_CONTROL_COMMAND_UPDATE', 
             'CASE2SERVER_CASE_END',  
             'CASE2SERVER_ADD_CASE',          
             ]

import time, os
from Queue import Queue
import threading
import re
import os,time , datetime
import socket
class CCommunicator(object):
    Type = 'server'
    Host = 'localhost'
    Port = 50000
    Sock = None
    Data4Case={}
    Data4Web={}
    ErrorInfo = Queue()
    ManualRunCase={}
    RunningSuite={}
    #===========================================================================
    # Data4Case={'casename1':
    #           {'sut1': {'command':Queue(),},
    #             },
    #           'casename2':
    #           {'sut1': {'command':Queue(),},
    #            'sut2': {'command':Queue(),},
    #             },              
    #           'casename3':
    #           {'sut1': {'command':Queue(),},
    #            'sut2': {'command':Queue(),},
    #            'sut3': {'command':Queue(),}
    #             },
    #           
    #           }
    #===========================================================================
    def __init__(self,type='server', host='localhost', port=50001):
        self.Type   = str(type).lower()
        self.Host   = host#'192.168.37.222'#host
        self.Port   = int(port)
        import socket
        if self.Type =='server':
            self.Sock = socket.socket()
            #Binding socket to a address. bind() takes tuple of host and port.
            self.Sock.bind((host, int(port)))
            #Listening at the address
            self.Sock.listen(5) #5 denotes the number of clients can queue
        elif self.Type == 'case' or self.Type == 'webclient':
            pass #self.Sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#             self.Sock.connect((HOST,PORT))
#             self.Sock.send('hello, here is multi-threading!')
        else:
            print 'error: (type=%s, host=%s, port=%s)'%(type, host, port)
            raise '(type=%s, host=%s, port=%s)'%(type, host, port)
    def __del__(self):
        if self.Sock!=None:
            self.Sock.close()
#===============================================================================
#     def get_interface_ip(self, ifname):
#         if os.name != "nt":
#             import fcntl
#             import struct
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
#                                 ifname[:15]))[20:24])
# 
#     def get_lan_ip(self):
#         ip = socket.gethostbyname(socket.gethostname())
#         if ip.startswith("127.") and os.name != "nt":
#             interfaces = [
#                 "eth0",
#                 "eth1",
#                 "eth2",
#                 "wlan0",
#                 "wlan1",
#                 "wifi0",
#                 "ath0",
#                 "ath1",
#                 "ppp0",
#                 ]
#             for ifname in interfaces:
#                 try:
#                     ip = self.get_interface_ip(ifname)
#                     break
#                 except IOError:
#                     pass
#         return ip
#===============================================================================
    def DecodeTLV(self,recvdata):
        dlen = len(recvdata)
        if dlen <3:
            print 'CCommunicator::DecodeTLV()::recvdata=%s'%recvdata
            raise 'error::recvdata can\'t parse to a defined TLV, it\'s too short'
        else:
            global TYPE#=['NULL','COMMANDLIST','WEBSESSIONID' ,'SUTNAME','CASENAME', 'CASECOMMAND', 'SUTCOMMAND', 'SUTRAWDATA','SUTCMDLIST', 'CASERAWDATA', 'CASEERRORMSG']
            ttype   = recvdata[0]
            tlen    = recvdata[1]*256+recvdata[2]
            tvalue  = recvdata[3:tlen+3]
            if ttype ==1 or ttype==2:# COMMANDLIST
                ttype   = TYPE[ttype]
                cmdlst  = []
                lvalue  = len(tvalue)
                while lvalue>0:
                    clen = tvalue[0]
                    cmd = ''.join(tvalue[1:clen+1])
                    cmdlst.append(cmd)
                    lvalue=lvalue-clen-1
                    tvalue= tvalue[clen+1:]
                tvalue = cmdlst
            elif ttype<12:                
                ttype   = TYPE[ttype]
                tlen    = recvdata[1]*256+recvdata[2]
                tvalue  = recvdata[3:tlen]
            else:
                #for debug print "type %d is not defined. recvdata(%s)"%(ttype, recvdata)
                raise "type %d is not defined. recvdata(%s)"%(ttype, recvdata)
            tv = {ttype: tvalue}
            #for debug print 'TV: ',tv
            return tv
    def EncodeTLV(self,type,value):
        tlv =list()
        if type == 1 or type==2:            
            for cmd in value[::-1]:
                lcmd = len(cmd)
                cmd = list(cmd)
                for c in cmd[::-1]:
                    tlv.insert(0,c)
                tlv.insert(0,chr(lcmd))

        else:
            tlen    = len(value)
            for c in value[::-1]:
                    tlv.insert(0,c)
        tlv.insert(0, chr(len(tlv)%256))
        tlv.insert(0, chr(len(tlv)/256))
        tlv.insert(0,chr(type))    
        #for debug print 'TLV: ', tlv
        return tlv
    def EncodeNV(self,type, value):
        global TYPE
        type = str(type).upper()
        type = TYPE.index(type)
        return self.EncodeTLV(type, value)      
    def EncodeMSG(self, msgtype=0, tlvs={'COMMANDLIST':["cmd1 1", "cmd2 2"],'WEBSESSIONID':'webid1234'}):
        msg =[]
        lmsg = 0
        for key in tlvs.keys():
            tlv = self.EncodeNV(key, tlvs[key])
            lmsg =lmsg + len(tlv)
            for c in tlv[::-1]:
                msg.insert(0,c)
        msgend = self.EncodeNV('EOF', '')
        lmsg= lmsg+len(msgend)
        for c in msgend[::]:
            msg.append(c)
        msg.insert(0,chr(msgtype))
        
        #for debug print 'EncodeMSG::list ',msg
        msg = ''.join(e for e in msg)

        #msg = ''.join(chr(e) for e in msg)
        #msg.insert(0, lmsg%256)
        #msg.insert(0, lmsg/256)
        #for debug print 'EncodeMSG:: (',msg,')'
        return msg
    def DecodeMsg(self, data=[1, 1, 0, 14, 6, 'c', 'm', 'd', '1', ' ', '1', 6, 'c', 'm', 'd', '2', ' ', '2', 2, 0, 9, 'w', 'e', 'b', 'i', 'd', '1', '2', '3', '4']):
        #if type(data)!=type([]):
            
        data =list(data)
        #for debug print 'received msg:', data
        msgtype=int(ord(data[0]))
        data = data[1:]
        ldata = len(data)
        global MSGTYPE
        msg ={"MESSAGETYPE":MSGTYPE[msgtype]}
        global TYPE
        while ldata>0:
            if ldata >=3:
                ttype   = int(ord(data[0]))
                tlen    = int(int(ord(data[1]))*256+int(ord(data[2]))*1)
                tvalue  = data[3:3+tlen]
                data = data[3+tlen:]
                if TYPE[ttype] == "COMMANDLIST":
                    cmdlst =[]
                    lcmdlst = len(tvalue)
                    while lcmdlst:
                        lcmd = int(ord(tvalue[0]))
                        cmd  = tvalue[1:1+lcmd]
                        cmdlst.append(''.join(cmd))
                        lcmdlst= lcmdlst-1-lcmd
                        tvalue = tvalue[1+lcmd:]
                    tvalue = cmdlst
                else:
                    tvalue = ''.join(tvalue)
                msg.update({TYPE[ttype]:tvalue})
                ldata=ldata-3-tlen
            else:
                print "reveived a bad msg(%s)"%data
                raise
        #for debug print 'DecodeMsg:: ',msg
        return msg   
        
    def AddCase(self,casename,sutnamelist=[], webclientid=''):
        if self.Data4Case.has_key(casename):
            print 'case %s is existed, no case will be added!'
        else:
            self.Data4Case.update({casename:{}})
            self.Data4Case[casename].update({"COMMAND":Queue()})
            self.Data4Case[casename].update({"WEBCLIENT":[]})
            if webclientid!='':
                self.Data4Case[casename]['WEBCLIENT'].append(webclientid)
                if not self.Data4Web.has_key(webclientid):
                    self.Data4Web.update({webclientid:{}})
                    self.Data4Web[webclientid].update({casename:{'INFO':Queue()}})
            for sut in sutnamelist:
                self.Data4Case[casename].update({sut:Queue()})
                self.Data4Web[webclientid][casename].update({sut:Queue()})
                
            print 'AddCase()::',self.Data4Case
            print 'AddCase()::',self.Data4Web
            
    def RemoveCase(self, casename):
        weblist = self.Data4Case[casename]['WEBCLIENT']
        for webid in weblist:
            print 'RemoveCase()::casename: ',casename," webid: ", webid, ' ' ,self.Data4Web[webid].pop(casename)            
        print 'RemoveCase()::casename: ',casename,' ' ,self.Data4Case.pop(casename)
    def TxMsg2Server(self,msg):
        MAX_LENGTH_OF_MSG= 1024
        if self.Type!='server':
            try:
                import socket
                self.Sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.Sock.connect((self.Host,self.Port))
                block= int(len(msg)/MAX_LENGTH_OF_MSG)
                index = 0
                while index <=block:
                    self.Sock.send(str(msg[index*MAX_LENGTH_OF_MSG:(index+1)*MAX_LENGTH_OF_MSG]))
                    index =index+1
            except Exception, e:
                print e
        else:
            raise
    def RxServerMsg(self, length=1024):
        if self.Type!='server':
            try:
                return self.Sock.recv(length)
            except Exception, e:
                print e
        else:
            raise             
    def LogInfo(self,erromsg='',logtype ='error'):
        
        tm = time.strftime('%Y-%m-%d %H:%M:%S:',time.localtime())
        errorinfo = '%s\t%s\t%s'%(tm,logtype, erromsg)
        print errorinfo
        self.ErrorInfo.put(errorinfo)
    
    def GenSuiteReport(self):

        response ="""
<HTML>
<HEAD>
<TITLE>Suite Test Report</TITLE>
</HEAD>
<BODY>
<table cellspacing="1" cellpadding="2" border="1">
"""
        
        for key in self.RunningSuite.keys():
            basename = str(self.RunningSuite[key]['LOGDIR']).split('/')
            suitename = basename[len(basename)-2]
            dirtime = basename[len(basename)-1]
            suitelogdir ="/log/%s/%s"%(suitename,dirtime)
            response = response+ '<tr><td>SUITE NAME</td><td>%s</td></tr>'%(str(key))
            response = response +"""
    <tr><td>STATUS</td><td>%s</td></tr>
    <tr><td>RANGE</td><td>%s</td></tr>
    <tr><td>START TIME</td><td>%s</td></tr>
    <tr><td>END TIME</td><td>%s</td></tr>
    <tr><td>Running Case</td><td>%s</td></tr>
    <tr><td>Test Report</td><td>%s</td></tr>
    <tr><td>LOGDIR</td><td><a target='_BLANK' href='/log/%s/%s' >%s</a></td></tr>

"""%(                   str(self.RunningSuite[key]['STATUS']),
                      str(self.RunningSuite[key]['RANGE']),
                      str(self.RunningSuite[key]['STARTTIME']),
                      str(self.RunningSuite[key]['ENDTIME']),
                      str(self.RunningSuite[key]['RUNNINGCASE']),
                      str(self.RunningSuite[key]['TESTREPORT']),
                      #self.Host,
                      suitename,
                      dirtime,
                      str(self.RunningSuite[key]['LOGDIR'])
                      
                      )

            #===================================================================
            # caseresult= self.RunningSuite[key]['RESULT'].keys()
            # caseresultlist = sorted(caseresult)
            # for roc in caseresultlist:
            #     response=response+ '''%s\n'''%(self.RunningSuite[key]['RESULT'][roc])
            #===================================================================
        
        return response+"""</table>
<br />
<br />
</body></html>"""
    def HanleDataRequestFromWeb(self,requesttype):
        response = ''
        if str(requesttype).lower()=='runningsuite':
            response = self.GenSuiteReport()
        elif str(requesttype).lower()=='runningcase':
            response = '<p>Running Case</p>'
            for key in self.Data4Case.keys():
                response = response+ '<p>%s</p><br>'%(str(key))
                for subkey in self.Data4Case[key].keys():
                    response = response+ '<p>%s: %s</p><br>'%(str(subkey), str(self.Data4Case[key][subkey]))
            for key in self.Data4Web.keys():
                response = response+ '<p>%s</p><br>'%(str(key))
                for subkey in self.Data4Web[key].keys():
                    response = response+ '<p>%s: %s</p><br>'%(str(subkey), str(self.Data4Web[key][subkey]))
        else:
            print 'request type: ', requesttype
            raise
        
        return response
    def TxWEB2SERVER_SUTOUT_REQ(self,webid,casename,sutname):
        if self.Type != 'webclient':
            raise
        global MSGTYPE        
        msgtype = MSGTYPE.index('WEB2SERVER_SUTOUT_REQ', )
        data = self.EncodeMSG(msgtype, {'WEBSESSIONID'  : webid, 
                                        'CASENAME'      : casename,
                                        'SUTNAME'       : sutname})
        self.TxMsg2Server(data)
        return self.RxServerMsg()
    
    def RxWEB2SERVER_SUTOUT_REQ(self,conn, msg={}):
        if self.Type != 'server':
            raise
        #try:
        lock = threading.Lock()
        qsize = self.Data4Web[msg['WEBSESSIONID']][msg['CASENAME']][msg['SUTNAME']].qsize()
        response =''
        while qsize >0:
            response = response + self.Data4Web[msg['WEBSESSIONID']][msg['CASENAME']][msg['SUTNAME']].get()
            qsize =self.Data4Web[msg['WEBSESSIONID']][msg['CASENAME']][msg['SUTNAME']].qsize()
        #for debug print 'SERVER 2 WEB%s: ('%(str(conn)),response,')'
        global MSGTYPE        
        msgtype = MSGTYPE.index('SERVER2WEB_SUTOUT_RESP')
        if len(response)==0:
            response=''
        response = self.EncodeMSG(msgtype, tlvs={'SUTRAWDATA':response})
        conn.send(response)

    def TxWEB2SERVER_COMMAND_UPDATE(self,webid,casename,cmd,expect='',waittime=1,sutname=None):
        if self.Type != 'webclient':
            raise
        global MSGTYPE        
        msgtype = MSGTYPE.index('WEB2SERVER_COMMAND_UPDATE')
        if sutname ==None:
            data = self.EncodeMSG(msgtype, {'WEBSESSIONID'  : webid, 
                                            'CASENAME'      : casename,
                                            #'SUTNAME'       : sutname,
                                            'COMMAND'       : cmd,
                                            'EXPECT'        : expect,
                                            'WAITTIME'      : waittime
                                            }
                              )
        else:
            data = self.EncodeMSG(msgtype, {'WEBSESSIONID'  : webid, 
                                            'CASENAME'      : casename,
                                            'SUTNAME'       : sutname,
                                            'COMMAND'       : cmd,
                                            'EXPECT'        : expect,
                                            'WAITTIME'      : waittime
                                            }
                              )
        self.TxMsg2Server(data)
        #return self.RxServerMsg()
    
    def RxWEB2SERVER_COMMAND_UPDATE(self,conn, msg={}):
        if self.Type != 'server':
            raise
        lock = threading.Lock()
        lock.acquire()
        index =self.Data4Case[msg['CASENAME']]['WEBCLIENT'].index(msg['WEBSESSIONID'])
        exp =''
        wt  = 0
        if msg.has_key('EXPECT'):
            exp = msg['EXPECT']
        if msg.has_key('WAITTIME'):
            wt = msg['WAITTIME']
        lock = threading.Lock()
        if msg.has_key('SUTNAME'):
            self.Data4Case[msg['CASENAME']]['COMMAND'].put(['SUT',msg['SUTNAME'],msg['COMMAND'],exp, wt])
        else:
            self.Data4Case[msg['CASENAME']]['COMMAND'].put(['CASE',msg['COMMAND'],exp, wt]) 
        lock.release()
        #conn.send('SUCCESS\r\n')
        #=======================================================================
        # q = self.Data4Case[msg['CASENAME']]['COMMAND']
        # print 'SERVER:CASE %s:COMMAND:\n'
        # while q.qsize()>0:
        #     print q.get(),'\n'
        # print 'SERVER:CASE %s:COMMAND END'
        #=======================================================================
    def TxCASE2SERVER_SUTOUT_UPDATE(self,casename,sutname,data):    
        if self.Type != 'case':
            raise
        global MSGTYPE   
             
        msgtype = MSGTYPE.index('CASE2SERVER_SUTOUT_UPDATE', )
        data = self.EncodeMSG(msgtype, {'CASENAME'          : casename, 
                                        'SUTNAME'           : sutname,
                                        'SUTRAWDATA'        : data
                                        })
        self.TxMsg2Server(data)
        #return self.RxServerMsg()
    def RxCASE2SERVER_SUTOUT_UPDATE(self,conn,msg={}):
        if self.Type != 'server':
            raise
        global MSGTYPE   
        lock = threading.Lock()     
        weblist = self.Data4Case[msg['CASENAME']]['WEBCLIENT']
        lock = threading.Lock()
        lock.acquire()
        for web in weblist:
            self.Data4Web[web][msg['CASENAME']][msg['SUTNAME']].put(msg['SUTRAWDATA'])
        lock.release()
        #return self.RxServerMsg()
    def TxCASE2SERVER_COMMAND_REQ(self,casename):
        if self.Type != 'case':
            raise
        global MSGTYPE        
        msgtype = MSGTYPE.index('CASE2SERVER_COMMAND_REQ' )
        #
        msg = self.EncodeMSG(msgtype, {'CASENAME'          : casename,
                                       'NULL':'NULL' } )
        #for debug print msg
        try:
            cmd =None
            self.TxMsg2Server(msg)
            rspmsg =self.RxServerMsg()
            if len(rspmsg):
                rspmsg =self.DecodeMsg(rspmsg)
                cmd = self.RxSERVER2CASE_COMMAND_RESP(rspmsg)
        except Exception, e:
            print e.message
        return cmd
    def RxCASE2SERVER_COMMAND_REQ(self,conn,msg={}):
        if self.Type != 'server':
            raise
        payload={}
        rspmsg=''
        msgtype = MSGTYPE.index('SERVER2CASE_COMMAND_RESP')
        lock = threading.Lock()
        lock.acquire()
        if self.Data4Case[msg['CASENAME']]['COMMAND'].qsize()==0:
            rspmsg = self.EncodeMSG(msgtype, {
                            'NULL'       : 'NULL',
                            }
                            )
        else:
            record =self.Data4Case[msg['CASENAME']]['COMMAND'].get()
            print 'command is %s, it is ready for sending to Case'%record       
            if record[0]== 'SUT':
                #self.Data4Web[msg['CASENAME']]['COMMAND'].put(['SUT',msg['SUTNAME'],msg['COMMAND'],exp, wt])
                rspmsg = self.EncodeMSG(msgtype, {
                                            'SUTNAME'       : record[1],
                                            'COMMAND'       : record[2],
                                            'EXPECT'        : record[3],
                                            'WAITTIME'       : record[4]
                                            }
                                            )
            elif record[0] == 'CASE':
                rspmsg = self.EncodeMSG(msgtype, {
                                            #'SUTNAME'       : record[1],
                                            'COMMAND'       : record[1],
                                            'EXPECT'        : record[2],
                                            'WAITTIME'       : record[3]
                                            }
                                            )
            else:
                raise
            print 'Tx Command2Case:%s'%str(rspmsg)
        lock.release()
        conn.send(rspmsg)
        
    def RxSERVER2CASE_COMMAND_RESP(self,msg={}):
        if self.Type!='case':
            raise
        global MSGTYPE
        
        if msg['MESSAGETYPE']!='SERVER2CASE_COMMAND_RESP':
            raise
        cmd=None
        if not msg.has_key('COMMAND'):
            return None
        
        if msg.has_key('SUTNAME'):
            cmd=['SUT'  ,msg['SUTNAME'],  msg['COMMAND'], msg['EXPECT'], msg['WAITTIME']]
        else:
            cmd=['CASE' ,None,           msg['COMMAND'], msg['EXPECT'], msg['WAITTIME']]
        return cmd
        

    def TxWEB2SERVER_CONTROL_COMMAND_UPDATE(self,webid,casename, command):
        if self.Type != 'webclient':
            raise
        global MSGTYPE        
        msgtype = MSGTYPE.index('WEB2SERVER_CONTROL_COMMAND_UPDATE', )
        
        data = self.EncodeMSG(msgtype, {'COMMAND'       : command, 
                                        'WEBSESSIONID'  : webid, 
                                        'CASENAME'      : casename,}
                                        )
        self.TxMsg2Server(data)
        return self.RxServerMsg()
    def RxWEB2SERVER_CONTROL_COMMAND_UPDATE(self,conn ,msg={}):
        if self.Type != 'server':
            raise
        response =''
        reManualRunCaseCMD = re.compile('manualruncase\s+(.+)', re.IGNORECASE)
        #runsuite Sanity_Petaluma.csv range 1-210
        reRunSuite = re.compile('\s*runsuite\s+(.+)\s+range\s+(.+)', re.IGNORECASE)
        reRunSuiteWithArgs = re.compile('\s*runsuite\s+(.+)\s+range\s+(.+)\s+args\s+(.*)', re.IGNORECASE)
        print 'RxWEB2SERVER_CONTROL_COMMAND_UPDATE ', msg
        msg['COMMAND']=str(msg['COMMAND']).replace('''%20''', ' ') 
        m = re.match(reManualRunCaseCMD, msg['COMMAND'])
        mRunSuite = re.match(reRunSuite , msg['COMMAND'])
        mRunSuiteWithArgs = re.match(reRunSuiteWithArgs , msg['COMMAND'])
        reRequestValue = re.compile('\s*get\s+(.+)\s*', re.IGNORECASE)
        mRequestValue = re.match(reRequestValue, msg['COMMAND'])
        if m:# benchfilename,sut1,sut2...
            print 'it is ManualRunCaseCMD'
            th =threading.Thread(target=self.ManaulRunCase,args =[msg])
            th.start()
            self.ManualRunCase.update({msg['CASENAME']:{}})
            self.ManualRunCase[msg['CASENAME']].update({'RESULT':'RUNNING'})
        elif mRunSuiteWithArgs:
            print 'it is RunSuiteCMD'
            suitename= mRunSuiteWithArgs.group(1)
            range = mRunSuiteWithArgs.group(2)
            args = mRunSuiteWithArgs.group(3)
            args = str(args).split(',')
            self.StartRunSuite(suitename, range, args)            
#===============================================================================
#         elif mRunSuite:
#             print 'it is RunSuiteCMD'
#             suitename= mRunSuite.group(1)
#             range = mRunSuite.group(2)
# 
#             self.StartRunSuite(suitename, range)
#===============================================================================
        elif mRequestValue:
            response =self.HanleDataRequestFromWeb(mRequestValue.group(1))
            
        conn.send(response)
    def LoadCSV2List(self, csvfilename, args=[]):
        import os,StringIO,csv
        import re as sre
        suite=[]
        suitefile = csvfilename
        if str(csvfilename).find(os.sep)==-1:#just file basename, no path name
            suitefile= "..%shtml%ssuite%s%s"%(os.sep,os.sep,os.sep,csvfilename)
        reComment    = sre.compile("^[\s]*#[\s]*[\S]*",sre.I)
        #reAttribute = sre.compile("^[\s]*([\S]+)[\s]*=[\s]*([\S]*)",sre.I)
        suite=[]
        lineindex = 0
        for line in open(suitefile, "r"):
            lineindex =lineindex+1
            if sre.match(reComment,line,sre.IGNORECASE):
                continue
            #line = " ".join(shlex.split(line,comments=True))
            #var[i][1]=str(var[i][1]).replace("${%d}"%(gi), str(self.ARGV[gi])) 
            index = 0
            for arg in args:
                line=str(line).replace("${%d}"%(index+1), arg)
                index=index +1
            reVar = re.compile('\s*.*\${\s*(\d+)\s*}\s*.*')
            mVar = re.match(reVar,line)
            if mVar:
                print 'This suite require Argument(s) replace in line(%d): %s'%(lineindex,line )
                raise
            line = StringIO.StringIO(line)
            
            reader = csv.reader(line,delimiter=',')
            for row in reader:
                r=[]
                for col in row:
                    r.append(col)
                suite.append(r)
        print 'Load testsuite ', csvfilename ,suite
        return suite
                                     
    def StartRunSuite(self,suitename,caserange, args=[]):
        import time, datetime
        suite = self.LoadCSV2List(suitename, args)
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        self.RunningSuite.update({suitename:{'STARTTIME':timestamp, 'ENDTIME':'-', 'RANGE':caserange}})
        print 'start to run test suite:', suitename
        print self.RunningSuite
        if str(caserange).upper()=='ALL':
            caserange = range(0, len(suite)-1)
        else:        
            caserange = str(caserange).strip()
            caserange = str(caserange).split(',')
            drange = []
            for i in caserange:
                if str(i).find('-')!=-1:
                    s,e =str(i).split('-')
                    i = range(int(s)-1,int(e))
                else:
                    i =[int(i)-1]
                drange =drange+i
            caserange= sorted(drange)
        print 'range of SUITE:', caserange

        timestamps = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        suitefilename = os.path.basename(os.path.abspath(suitename))
        logdir = '../html/log/%s'%suitefilename
        try:
            os.mkdir(os.path.abspath(logdir))
        except:
            pass
        logdir = '../html/log/%s/%s'%(suitefilename, timestamps)    
        os.mkdir(os.path.abspath(logdir))
        self.RunningSuite[suitename].update({'LOGDIR':logdir})        
        self.RunningSuite[suitename].update({'STATUS':'RUNNING'})  
        self.RunningSuite[suitename].update({'RESULT':{}})    
        th =threading.Thread(target=self.RunTestSuiteLoop,args =[suitefilename,suitename, suite,caserange , logdir, timestamps])
        th.start()
        
    def RunTestSuiteLoop(self,suitefilename ,suitename, suite,range , logdir, timestamps):
        suitelogdir = str(logdir).split('/')
        htmlsuitelogdir = "/log/%s/%s"%(suitelogdir[len(suitelogdir)-2],suitelogdir[len(suitelogdir)-1])
        reRETRY = re.compile('\s*try\s+(\d+)', re.I)
        suitereportfilename = '%s-%s.html'%(suitename,timestamps )
        
        
        response ="""
<HTML>
<HEAD>
<TITLE>Suite Test Report</TITLE>
</HEAD>
<BODY>
<table cellspacing="1" cellpadding="2" border="1">
<tr><td>SUITE NAME</td><td>%s</td></tr>"""%suitereportfilename
        reportfile = open('../html/log/%s/%s/%s'%(suitelogdir[len(suitelogdir)-2],suitelogdir[len(suitelogdir)-1],suitereportfilename), "w+")
        reportfile.write(response)
        self.RunningSuite[suitename].update({'TESTREPORT': '<a target="+BLANK" href="%s">%s</a>'%(htmlsuitelogdir+'/'+suitereportfilename,suitereportfilename)})  
        
        for index in range:
            self.RunningSuite[suitename].update({'RUNNINGCASE' :'%d/%s'%(index+1, suite[index][0] )})
            print 'RUN SUITE', suitefilename, ' index', index,'case:', suite[index]
            caselogdir = logdir+'/%d'%(index+1)
            htmlcasedir="%s/%d"%(htmlsuitelogdir, index+1)
            os.mkdir(os.path.abspath(caselogdir))
            casefailed = True
            starttime = time.time()
            if self.RunCase(suite[index], caselogdir):
                print 'FAIL: SUITE', suitefilename, ' index', index,'case:', suite[index]
                m = re.match(reRETRY,suite[index][2])
                if m :
                    retry = int(m.group(1))
                    while retry> 0  :
                        
                        casefailed = self.RunCase(suite[index], caselogdir)
                        if not casefailed:
                            print 'PASS with RETRY SUITE', suitefilename, ' index', index,'case:', suite[index], 'REMAINING RETRY TIME ',retry-1
                            break
                        
                        retry =retry -1
                        print 'FAIL SUITE', suitefilename, ' index', index,'case:', suite[index], 'REMAINING RETRY TIME ',retry
            else:
                casefailed= False
                print 'PASS SUITE', suitefilename, ' index', index,'case:', suite[index]
            endtime = time.time()
            duration = endtime-starttime
            duration= str(datetime.timedelta(seconds=int(duration)))
            record =''
            if casefailed:
                print 'FAIL SUITE', suitefilename, ' index', index,'case:', suite[index]
                record = '<tr><td>%d'%(index+1)+ '<td bgcolor="#FF0000"><a  target="+BLANK" href="%s">'%htmlcasedir+'FAIL</a></td> <td>'+str(suite[index][0])+'</td> <td>'+str(caselogdir)+'</td><td>'+duration+' </td></tr>\n' 
                self.RunningSuite[suitename]['RESULT'].update({index+1:record})
                reportfile.write(record)
               
                if suite[index][1].upper()=='ABORT' or suite[index][1].upper()=='SKIP':
                    print 'TERMINATED SUITE BY KEY CASE FAILED', suitefilename, ' index', index,'case:', suite[index]
                    self.RunningSuite[suitename].update({'STATUS':'TERMINATED'}) 
                    break
                 
            else:
                record = '<tr><td>%d'%(index+1)+ '</td><td bgcolor="#00FF00"><a  target="+BLANK" href="%s">'%htmlcasedir+'FAIL</a></td><td>'+str(suite[index][0])+'</td><td>'+str(caselogdir)+'</td><td>'+duration+' </td> </tr>'
                self.RunningSuite[suitename]['RESULT'].update({index+1:record})
                print self.RunningSuite[suitename]
                reportfile.write(record)

        record= """</table>
<br />
<br />
</body></html>"""
        reportfile.write(record)
        reportfile.close()
        if self.RunningSuite[suitename]['STATUS']=='RUNNING':
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            self.RunningSuite[suitename].update({'ENDTIME':timestamp})  
            self.RunningSuite[suitename].update({'STATUS':'DONE'})  
            
                
    def ManaulRunCase(self,msg):
        reManualRunCaseCMD = re.compile('manualruncase\s+(.+)', re.IGNORECASE)
        m = re.match(reManualRunCaseCMD, msg['COMMAND'])
        if m:
            cmd = m.group(1).strip()
            import StringIO,csv
            cmd = StringIO.StringIO(cmd)
            reader = csv.reader(cmd,delimiter=',')
            r=[]
            for row in reader: 
                for element in row:
                    r.append(element.strip())
            benchname = r[0]
            suts = r[1:]
            self.AddCase(msg['CASENAME'], suts, msg['WEBSESSIONID'])
            #['./TestCase/SeedCDCN2.py R07.02.081_C7M8U_401_0000 192.168.1.200 ', 'ABORT', ''],
            cmd= './ManualRunCase.py %s %s '%(msg['CASENAME'],benchname)
            for sut in suts:
                cmd= cmd + '%s '%sut
                
            self.RunCase([cmd,'',''], "../html/log/mr")

    def RunCase(self, case=[],logdir="../html/log/mr"):
        import tempfile, subprocess
        pipe_input ,file_name =tempfile.mkstemp()
        exe_cmd = " "
        if str(case[0]).find(".py") !=-1:
            
            #if str(case[0]).find(";([0-9.])")!=-1:
            #print str(case[0])
            rePythonVersion = re.compile(".+?;([0-9]+\.[0-9]+)\s*$", re.M)
            m = re.match(rePythonVersion, str(case[0]),re.M|re.MULTILINE)
            
            if m!=None:
                #print str(m.group(1))
                case[0] = str(case[0])[ 0:str(case[0]).find(";")]
                exe_cmd = "python%s "%(str(m.group(1)))
            else:
                exe_cmd = "python "
        else:
            exe_cmd = " "
        #print exe_cmd        
               
        pp = subprocess.Popen(args = exe_cmd+ case[0]+logdir,shell =True, stdin=pipe_input)
        
        ChildRuning = True
        while ChildRuning:
            if pp.poll() is None:
                interval = 1
                time.sleep(interval)
            else:
                #return pp.returncode:
                ChildRuning = False    
        return pp.returncode #non-zero means failed            
        #for debug print 'SERVER 2 WEB%s: ('%(str(conn)),response,')'
               
    def StartTcpServer(self):
        if self.Type=='server':
            import threading

            while True:
            #Accepting incoming connections
                try:
                    conn, addr = self.Sock.accept()
                #Creating new thread. Calling clientthread function for this function and passing conn as argument.
                    #for debug print "Receive %s's TCP request"%str(addr)
                    th =threading.Thread(target=self.Wait4ClientRequest,args =[conn])
                    th.start()
                    #conn.close()
                
                except Exception, e:
                    print e
                    self.LogInfo(e.message)
        else:
            print "this is a client, not a server, StartServer() has nothing to do"  
            
            raise
    def TxCASE2SERVER_CASE_END(self,casename,testresult):
        if self.Type != 'case':
            raise        
        global TYPE, MSGTYPE
        msg = self.EncodeMSG(MSGTYPE.index('CASE2SERVER_CASE_END'), {'CASENAME'      : casename,
                                                                     'CASERESULT': testresult}
                             )
        self.TxMsg2Server(msg)  
    def RxCASE2SERVER_CASE_END(self,conn,msg={}):
        if self.Type != 'server':
            raise        
        print msg['CASENAME'],'ENDED WITH RESULT=',msg['CASERESULT']
        rslt=msg['CASERESULT']
        if rslt.strip=='':
            rslt = 'ENDED'
        self.ManualRunCase[msg['CASENAME']].update({'RESULT':rslt})
        time.sleep(10)#for webclient to get all data in buffer, maybe it should be more longer
        self.RemoveCase(msg['CASENAME'])
    def TxCASE2SERVER_ADD_CASE(self,casename,sutlist,logdir):
        if self.Type != 'case':
            raise        
        global TYPE, MSGTYPE
        msg = self.EncodeMSG(MSGTYPE.index('CASE2SERVER_ADD_CASE'), {
                                                                     'CASENAME'      : casename,
                                                                     'SUTNAMELIST': sutlist,
                                                                     }
                             )
        self.TxMsg2Server(msg)     
    def RxCASE2SERVER_ADD_CASE(self,conn,msg={}):
        if self.Type != 'server':
            raise        
        print 'RxCASE2SERVER_ADD_CASE ',msg
        casename = msg['CASENAME']
        sutnamelist = msg['SUTNAMELIST']
        self.AddCase(casename, sutnamelist)

              
    def Wait4ClientRequest(self,conn):
        if self.Type=='server':
            try:
                global MSGTYPE
                rcvdata = conn.recv(1024*100) # 1024 stands for bytes of data to be received
                fMsgNotEnd=True 
                msg={}
                while fMsgNotEnd:                    
                    try:
                        msg =self.DecodeMsg(rcvdata)
                    except:
                        pass
                    if msg.has_key('EOF'):
                        fMsgNotEnd=False
                    else:
                        data = conn.recv(1024*100)
                        rcvdata= rcvdata+data
                       
                #for debug print msg
             #==================================================================
             #    'NULL',
             # 'WEB2SERVER_SUTOUT_REQ',#'SERVER2WEB_SUTOUT_RESP',
             # 'CASE2SERVER_SUTOUT_UPDATE',#'SERVER2CASE_SUTOUT_UPDATE_ACK',
             # 'WEB2SERVER_COMMAND_UPDATE',#'SERVER2WEB_COMMAND_ACK',
             # #'WEB2SERVER_CASE_COMMAND_UPDATE',
             # 'CASE2SERVER_COMMAND_REQ',
             # 'SERVER2CASE_COMMAND_RESP', 
             #==================================================================
                if msg['MESSAGETYPE']=='NULL':
                    print 'Wait4ClientRequest: Received a NULL message'
                elif msg['MESSAGETYPE'] == 'WEB2SERVER_SUTOUT_REQ' :
                    self.RxWEB2SERVER_SUTOUT_REQ(conn,msg)
                elif msg['MESSAGETYPE'] == 'CASE2SERVER_SUTOUT_UPDATE' :
                    self.RxCASE2SERVER_SUTOUT_UPDATE(conn, msg)
                elif msg['MESSAGETYPE'] == 'WEB2SERVER_COMMAND_UPDATE':
                    print 'Rx WEB2SERVER_COMMAND_UPDATE: %s'%str(msg)
                    self.RxWEB2SERVER_COMMAND_UPDATE(conn, msg)                
                elif msg['MESSAGETYPE'] == 'CASE2SERVER_COMMAND_REQ' :
                    #print 'Rx Case2SERVER_COMMAND_REQUEST: %s'%str(msg)
                    self.RxCASE2SERVER_COMMAND_REQ(conn, msg)
                elif msg['MESSAGETYPE'] == 'WEB2SERVER_CONTROL_COMMAND_UPDATE' :
                    #print 'Rx Case2SERVER_COMMAND_REQUEST: %s'%str(msg)
                    print 'Rx WEB2SERVER_CONTROL_COMMAND_UPDATE',msg
                    self.RxWEB2SERVER_CONTROL_COMMAND_UPDATE(conn, msg)
                elif msg['MESSAGETYPE'] == 'CASE2SERVER_CASE_END' :
                    #print 'Rx Case2SERVER_COMMAND_REQUEST: %s'%str(msg)
                    print 'Rx CASE2SERVER_CASE_END',msg
                    self.RxCASE2SERVER_CASE_END(conn, msg)   
                elif msg['MESSAGETYPE'] == 'CASE2SERVER_ADD_CASE' :
                    #print 'Rx Case2SERVER_COMMAND_REQUEST: %s'%str(msg)
                    print 'Rx CASE2SERVER_CASE_END',msg
                    self.RxCASE2SERVER_ADD_CASE(conn, msg)                                      
                else:
                    raise
            except Exception, e:
                print "ERROR!!!!!!!!!!!!!!!!!!!",e
                conn.close()
                time.sleep(2)

        else:
            print "this is a server, works in passive mode, waiting for client(s) request, and reply client(s)"  
            gdata=data
            self.EncodeMSG(tlvs={'NULL':"NULL"})
            conn.send("%d %s"%(1,gdata))
            print data
        conn.close()

     
if __name__ == "__main__":
    import sys
    server = CCommunicator('server',sys.argv[1] )
    msg =server.EncodeMSG(1 )
    print msg
    msg =server.DecodeMsg(msg)
    print msg
    #msg ={'WEBSESSIONID': 'webid20140424_222208', 'COMMAND': 'runsuite Sanity_Petaluma.csv range 1,3, 5,6-8', 'CASENAME': 'suite20140424_222208', 'MESSAGETYPE': 'WEB2SERVER_CONTROL_COMMAND_UPDATE'}
    # {'WEBSESSIONID': 'webid20140424_214101', 'COMMAND': 'runsuite Sanity_Petaluma.csv range 1-210', 'CASENAME': 'suite20140424_214101', 'MESSAGETYPE': 'WEB2SERVER_CONTROL_COMMAND_UPDATE'}
    #server.RxWEB2SERVER_CONTROL_COMMAND_UPDATE(None, msg)
    server.StartTcpServer()


    


