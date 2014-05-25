#!/usr/bin/env python 
import cgi, cgitb
print "Content-Type: text/html\n"     # HTML is following
cgitb.enable()
form = cgi.FieldStorage()
bedname = form.getvalue('bedname')
if bedname==None:
    bedname = 'CDC_SIT.csv'
bench = '../html/bed/%s'%bedname
from dash import CDASHCase
import os
import re as sre
import csv
import shlex
import StringIO
def LoadBenchInfo( BENCH):
    BenchInfo={}
    benchfile = BENCH
    if str(BENCH).find(os.sep)==-1:#just file basename, no path name
        benchfile= ".%sTestCase%s%s"%(os.sep,os.sep,BENCH)
    reComment    = sre.compile("^[\s]*#[\s]*[\S]*",sre.I)
    reAttribute = sre.compile("^[\s]*([\S]+)[\s]*=[\s]*([\S]*)",sre.I)
    for line in open(benchfile, "r"):
        if sre.match(reComment,line,sre.IGNORECASE):
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
                BenchInfo.update({str(r[0]):{}})
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
                            BenchInfo.update({r[0]:str(value)})
                        else:
                            break
                    else:
                        BenchInfo[r[0]][name]=str(value)
                    counterCol =counterCol+1
    return BenchInfo
                
#print '*'*80

benchinfo = LoadBenchInfo(bench)
#print benchinfo
keys = sorted(benchinfo.keys())


sutliststring = ''
sut =[]
for key in keys:
    if type(benchinfo[key])==type({}):
        sut.append(key)
        line = '''<input id="sutid" type="checkbox"  name="sutid" value="%s" /> %s<br/>\n'''%(key,key)
        sutliststring = sutliststring+line
htmlstring ="""
<HTML>
<HEAD>
<TITLE>Test Bench List </TITLE>
<SCRIPT>
    function getChecked(){
        var chk_arr =  document.getElementsByName("sutid");
        var chklength = chk_arr.length;  
        var selected =encodeURI('a=b') ;         
        for(k=0;k< chklength;k++)
        {
            if (chk_arr[k].checked){                
                selected+=encodeURI('&sutid=')+encodeURI(chk_arr[k].value);                        
            }
        } 
        return selected;
    
    }

        function post( id, dest, params )
        {
            var xmlhttp;

            if (window.XMLHttpRequest)
            {// code for IE7+, Firefox, Chrome, Opera, Safari
                xmlhttp=new XMLHttpRequest();
            }
            else
            {// code for IE6, IE5
                xmlhttp=new ActiveXObject('Microsoft.XMLHTTP');
            }

            xmlhttp.onreadystatechange=function()
            {
                if (xmlhttp.readyState==4 && xmlhttp.status==200)
                { 
                    newHTML( xmlhttp.responseText);
                    setTimeout("window.close()",3000); 
                }        
            }
            xmlhttp.open("POST",dest,true);
            xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
            xmlhttp.send( params ); 
        }

    function newHTML(HTMLstring) {
        //var checkitem = mygetCheckedItem();
        //HTMLstring=post( 'manualtest','/cgi-bin/onManualCaseRun.py', 'bedname='+encodeURI(checkitem) );    
        var newwindow=window.open();
        var newdocument=newwindow.document;
        newdocument.write(HTMLstring);
        newdocument.close();
    }
    function onSUTSelected(benchname){
        var checked = getChecked()
        post( 'manualtest','/cgi-bin/onManualCaseRun.py', 'bedname='+encodeURI(benchname)+'&'+checked ); 
    }
</SCRIPT>
</HEAD>
<BODY>
<FORM NAME='mainform'>
<U>Select SUT(s)</U>
<BR>
%s
<BR>
<INPUT TYPE='BUTTON' VALUE='New Window' onclick='onSUTSelected("%s");'>
</FORM>
</BODY>
</HTML>"""%(sutliststring, bench)
print htmlstring
