#!/usr/bin/env python 
#from pexpect import spawn
import pexpect
import time,sys,os,StringIO,csv
from CCommunicator import CCommunicator
from CTestCase import CTestCase
import re as sre

class CCase(CCommunicator):
    steps=[]
    childt=None
    bEndCase=False
    BENCH =''
    CASENAME=''
    BenchInfo={}
    SUTNAME=[]
    CASE=None
    CurrentTarget= '' # '' is the default, target is case itself, otherwise it should be the SUT name
    RecordReplay = []
    CaseDir='../html/case/' 
    LogDir='../html/log/mr/' 
    def AddCmd2RecordReplay(self,cmd):
        newrecord = cmd[1:]
        if cmd[0]=='CASE':
            newrecord[0]='''#%s'''%newrecord[0]
        for sut in self.SUTNAME:
            newrecord.append('')
        self.RecordReplay.append(newrecord)
    def UpdateSutOutput2RecordReplay(self, sutname, data):
        colIndex = 4   +  self.SUTNAME.index(sutname )
        rowIndex = len(self.RecordReplay)-1
        while len (self.RecordReplay[rowIndex])<colIndex+2:            
            self.RecordReplay[rowIndex].append('')
        self.RecordReplay[rowIndex][colIndex] = '''%s'''%(self.RecordReplay[rowIndex][colIndex]+ data)
    def SaveCase2File(self):
        import csv    
        out = csv.writer(open(self.CaseDir+'/'+self.CASENAME+'.csv',"w+"), delimiter=',',quoting=csv.QUOTE_ALL)
        for i in self.RecordReplay:
            out.writerow(i)
        out.writerow(['#!---'])
        
    def LoadBenchInfo(self):

        if self.BenchInfo!={}:#ever loaded bench info before
            pass #return self.BenchInfo[str(var)]
        else:   #never loaded bench info before
            benchfile = self.BENCH
            print 'benchfile:', benchfile
            if str(self.BENCH).find(os.sep)==-1:#just file basename, no path name
                benchfile= self.BENCH
            self.reComment    = sre.compile("^[\s]*#[\s]*[\S]*",sre.I)
            self.reAttribute = sre.compile("^[\s]*([\S]+)[\s]*=[\s]*([\S]*)",sre.I)
            for line in open(benchfile, "r"):
                if sre.match(self.reComment,line,sre.IGNORECASE):
                    continue
                #line = " ".join(shlex.split(line,comments=True))
                line = StringIO.StringIO(line)
                reader = csv.reader(line,delimiter=',')
                r =[]
                #print "="*100,"\n",s,"\n"
                for row in reader:                            
                    for element in row:
                        r.append(element.strip())
                    if len(r)<2:
                        raise Exception("VAR (%s) in Bench (%s) has NOT been assigned"%(str(r[0]),benchfile))
                    elif len(str(r[0]).strip()) ==0:
                        continue #no variable name in 1st column, ignore this line
                    else:
                        self.BenchInfo.update({str(r[0]):{}})
                        if str(r[0])== "AMP":
                            pass
                        counterCol = 1
                        for attr in r[1:]:
                            name =""
                            value = ""
                            index = str(attr).find("=")
                            if index >1:
                                name = str(attr[:index]).strip()
                                value = str(attr[index+1:]).strip()
                            else:# index ==0 or -1:#string started with "=", or no "=" found
                                value =str(attr).strip()
                            if len(name)==0:
                                if counterCol==1:
                                    self.BenchInfo.update({r[0]:str(value)})
                                else:
                                    break
                            else:
                                self.BenchInfo[r[0]][name]=str(value)
                            counterCol =counterCol+1

        #print str(self.BenchInfo)

    
    def __init__(self, casename,benchname, sutnames=[]):
        self.CASENAME = casename
        self.SUTNAME= sorted(sutnames)
        self.BENCH = benchname
        self.LoadBenchInfo()
        bench =self.BenchInfo
        suts = {}
        self.RecordReplay = [['[cs]'], ['#VAR'],['#SETUP']]
        newrecord = ['#SUTNAME', 'COMMAND', 'EXPECT', 'WAIT TIME(s)']
        for sut in self.SUTNAME:
            if bench.has_key(sut) and type(bench[sut])== type({}):
                suts.update({sut: bench[sut]})
                newrecord.append(sut+' OUTPUT')
        self.RecordReplay.append(newrecord)
        self.RecordReplay.append(['#'])
        #__init__(self, casename = "TestCaseName",sut={}, provision=[], run=[], teardown=[], exception="",LogPath = ""):
        self.CASE = CTestCase(casename,suts,[],[],[],'',self.LogDir)
        CCommunicator.__init__(self, 'case')
    def CaseCommand(self,casecommand):
        reEndCase =sre.compile('\s*set\s+caseresult\s+(.+)\s*', sre.IGNORECASE)
        print 'CASE command:',str(casecommand)
        m =sre.match(reEndCase, casecommand)
        if m:
            print 'End Test Case!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            self.EndTestCase(m.group(1))
        else:
            print 'CASE COMMAND(%s) is NOT defined!!!! '%casecommand
        
    def EndTestCase(self,result=''):
        self.bEndCase= True
        self.TxCASE2SERVER_CASE_END(self.CASENAME, result)
        self.SaveCase2File()
    def runcase(self):
        import threading
        self.childt=threading.Thread(target=self.comproc)
        
        self.childt.start()
        time.sleep(1)
        while not self.bEndCase:
            try:
                try:
                    pass
                          
                except:
                    pass
                time.sleep(0.8)
            except Exception,e:
                print e.message,e.value
                self.bEndCase=True
    def HandleCmdIn(self,rawdata):
        self.steps=rawdata
        reCaseCommand = sre.compile('\s*cc\s*,\s*(.*)', sre.IGNORECASE)
        reChange2SUT = sre.compile('\s*sc\s*,\s*(.*)\s*(,*)\s*', sre.IGNORECASE)
        reSUTCommand = sre.compile('\s*sc\s*,\s*(.+)\s*,\s*(.*)', sre.IGNORECASE)
        self.AddCmd2RecordReplay(self.steps)
        if len(self.steps)!=0:
            if self.steps[0]=='CASE':
                print 'HandleCmdIn::%s'%str(self.steps)
                mCase = sre.match(reCaseCommand, self.steps[2])
                mChg2Sut = sre.match(reChange2SUT, self.steps[2])
                mSut = sre.match(reSUTCommand, self.steps[2])
                if mCase:
                    print 'Rx case command' ,mCase.group(1)
                    self.CurrentTarget = ''
                    self.CaseCommand(mCase.group(1))

                
                elif mSut:
                    print 'Rx Target Change to SUT & CMD:' ,mSut.group(1), mSut.group(2)
                    sutname = mSut.group(1).strip()
                    if self.CASE.SUTs.has_key(sutname):
                        self.CurrentTarget = sutname
                        cmd = mSut.group(2)
                    else:
                        self.CASE.logger.error('SUT Name is wrong:(%s)\nRAW COMMAND(%s)'%(mSut.group(1), str(rawdata)))  
                    
                    self.CASE.SUTs[sutname].ActionCheck(cmd,'',0.2)
                elif mChg2Sut:
                    print 'Rx Target Change to SUT:' ,mChg2Sut.group(1)
                    sutname = mChg2Sut.group(1)
                    if self.CASE.SUTs.has_key(sutname):
                        self.CurrentTarget = mChg2Sut.group(1)
                    else:
                        self.CASE.logger.error('SUT Name is wrong:(%s)\nRAW COMMAND(%s)'%(mChg2Sut.group(1), str(rawdata)))   
                else:
                    print 'HandleCmdIn RxCmd: ', self.steps
                    if self.CurrentTarget=='':
                        self.CaseCommand(self.steps[2])
                    else:
                        #self.CASE.SUTs[self.CurrentTarget].ActionCheck(self.steps[2],'',1)
                        self.CASE.SUTs[self.CurrentTarget].sendline(self.steps[2])#(self.steps[2],'',1)

            else:
                #self.CASE.SUTs[self.steps[1]].ActionCheck(self.steps[2])

                self.CASE.SUTs[self.steps[1]].sendline(self.steps[2])
            self.steps=[]        
    def comproc(self):

        while not self.bEndCase :
            #print time.strftime("%Y-%m-%d_%H:%M:%S 1", time.localtime())
            cmd = self.TxCASE2SERVER_COMMAND_REQ(self.CASENAME)
            if type(cmd)!=type(None):
                print 'child command : ', cmd
                self.HandleCmdIn(cmd)
            for sutname in self.SUTNAME:
#                print 'sut:', sutname
#                print self.SUTNAME
                
                self.CASE.SUTs[sutname].send('')
                try:                    
                    self.CASE.SUTs[sutname].expect('.*|pexpect.TIMEOUT',0.2, False)  
                except Exception, e:
                    print e
                    pass
                if self.CASE.SUTs[sutname].match:
                    print 'match:',self.CASE.SUTs[sutname].match.group(0)
                    self.TxCASE2SERVER_SUTOUT_UPDATE(self.CASENAME, sutname, str(self.CASE.SUTs[sutname].match.group(0)))
                    self.UpdateSutOutput2RecordReplay(sutname, self.CASE.SUTs[sutname].match.group(0))
                    self.CASE.SUTs[sutname].match=None
                #time.sleep(0.2)




if __name__ == "__main__":
    import sys
    returncode = 0
    print 'sys.argv:',sys.argv
    casename = sys.argv[1]
    benchname = sys.argv[2]
    sutnames = sys.argv[3:len(sys.argv)-1]

        #    def __init__(self, casename = "TestCaseName",sut={}, provision=[], run=[], teardown=[], exception="",LogPath = ""):#/net/petnaf01/vol/vol1/ntshared/Software/C7_General/PET/Logs"

    case=CCase(casename,benchname,sutnames)

    case.runcase()
#===============================================================================
#     case = CCommunicator('case')
#     #web =CCommunicator('webclient')
#     counter =1
#     #case.TxCASE2SERVER_SUTOUT_UPDATE("casename2", "sut1", "SUT1:%d\r\n"%counter)
#     #case.TxCASE2SERVER_SUTOUT_UPDATE("casename2", "sut1", "SUT1:%d\r\n"%2)
#     print 'command : ', case.TxCASE2SERVER_COMMAND_REQ('casename2')
# 
#     while counter :
#         case.TxCASE2SERVER_SUTOUT_UPDATE("casename2", "sut1", "SUT1:%d\nnewline"%counter)
#         case.TxCASE2SERVER_SUTOUT_UPDATE("casename2", "sut2", "SUT2:%d"%counter)
#         cmd = case.TxCASE2SERVER_COMMAND_REQ('casename2')
#         if type(cmd)!=type(None):
#             print 'command : ', cmd
#         counter=counter+1
#         import time
#         time.sleep(1)
#===============================================================================
