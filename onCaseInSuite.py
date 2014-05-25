#!/usr/bin/env python 
import cgi, cgitb
print "Content-Type: text/html\n"     # HTML is following
cgitb.enable()
form = cgi.FieldStorage()
suitename = form.getvalue('suitename')
if suitename==None:
    suitename = 'Sanity_Petaluma.csv'
suite = '../html/suite/%s'%suitename
suite= '../html/suite/Sanity_Petaluma.csv'
from dash import CDASHCase
import os
import re as sre
import csv
import shlex
import StringIO

def LoadCSV2List(csvfilename):
    suite=[]
    suitefile = csvfilename
    if str(csvfilename).find(os.sep)==-1:#just file basename, no path name
        suitefile= "..%shtml%ssuite%s%s"%(os.sep,os.sep,os.sep,csvfilename)
    reComment    = sre.compile("^[\s]*#[\s]*[\S]*",sre.I)
    #reAttribute = sre.compile("^[\s]*([\S]+)[\s]*=[\s]*([\S]*)",sre.I)
    suite=[]
    for line in open(suitefile, "r"):
        if sre.match(reComment,line,sre.IGNORECASE):
            continue
        #line = " ".join(shlex.split(line,comments=True))
        line = StringIO.StringIO(line)
        
        reader = csv.reader(line,delimiter=',')
        for row in reader:
            r=[]
            for col in row:
                r.append(col)
            suite.append(r)
    return suite

suite = LoadCSV2List(suite)
rangebutton = '''<form name="f1" onsubmit="onSuiteSelectedRun(); return false;"> 
<p>Case Range: <input id="caserange" name="caserange" type="text" value="%d-%d" rows="1" cols="1" />  
<p>ARGs: <input id="suiteargs" name="suiteargs" type="text" value="" rows="1" cols="1" />  
  <input name="go" value="Run" type="button" onClick="onSuiteSelectedRun();"></p>
</form>'''%(1,len(suite))
caselines = '<table border="1" width="100%" >\n<tr>\n<th>No.</th><th>CASE NAME</th><th>Action when Case Failed</th><th>MAX RETRY TIMES</th></tr>\n'
index = 1
for  case in suite:
    line = """<tr> <td>%d</td> <td>%s</td> <td> %s </td> <td> %s </td> </tr>\n"""%(index,case[0],case[1],case[2])
    index=index+1
    caselines = caselines+line
htmlstring ="""
<HTML>
<HEAD>
<TITLE>Test Bench List </TITLE>
<SCRIPT>
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
                    setTimeout("window.close()",3000); 
                }        
            }
            xmlhttp.open("POST",dest,true);
            xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
            xmlhttp.send( params ); 
        }
        
    function onSuiteSelectedRun(){
        var caserange = document.getElementById('caserange');
        var suiteargs = document.getElementById('suiteargs');
        var suiteargsstring= suiteargs.value
        var rangestring =caserange.value;
        //alert(rangestring);
        var thestring = 'cmd='+encodeURI('runsuite %s range '+rangestring + ' args '+ suiteargsstring);
        //alert(thestring);
        post( 'suiteselect','/cgi-bin/Web2ServerCmd.py', thestring ); 
        
    }
</SCRIPT>
</HEAD>
%s
%s
</FORM>
</BODY>
</HTML>"""%(suitename,rangebutton,caselines)
print htmlstring
