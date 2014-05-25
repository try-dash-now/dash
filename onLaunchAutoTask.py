#!/usr/bin/env python 
#from CCommunicator import CCommunicator
import cgi, cgitb
print "Content-Type: text/html\n"     # HTML is following
cgitb.enable()
form = cgi.FieldStorage()

#print                               # blank line, end of headers
from os import listdir
from os.path import isfile, join

reqtype = form.getvalue('REQIRETYPE')
#if reqtype==None:
#    reqtype='bed'
path = '../html/%s/'%reqtype
suitelist=''
if reqtype== 'suite':
    onlyfiles = [ f for f in listdir(path) if isfile(join(path,f)) ] 
    onlyfiles = sorted(onlyfiles)
    CHECKED = 'CHECKED'

    for suite in onlyfiles:
        line = '<input type="radio" name="suitename" value="%s" %s/> %s </a><br>\n'%(suite,CHECKED,suite)
        CHECKED =''
        suitelist = suitelist+line

htmlstring ="""<HTML>
<HEAD>
<TITLE>Test Suite</TITLE>
<SCRIPT>
    function mygetCheckedItem()
    {
        var selectitem ='No Bench selected, please select one and continue';
        var x = document.getElementsByName('suitename');
        
        for(var k=0;k<x.length;k++){
          if(x[k].checked){
            selectitem = x[k].value;
            break;
          }
        }
        return selectitem;
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
        //HTMLstring=post( 'manualtest','/cgi-bin/onSUTLIST.py', 'suitename='+encodeURI(checkitem) );    
        var newwindow=window.open();
        var newdocument=newwindow.document;
        newdocument.write(HTMLstring);
        newdocument.close();
    }
    function onSuiteSelected(){
    var checkitem = mygetCheckedItem();
    post( 'manualtest','/cgi-bin/onCaseInSuite.py', 'suitename='+encodeURI(checkitem) );  
    
    }
</SCRIPT>
</HEAD>
<BODY>
<FORM NAME='mainform'>
<U>Select test bench</U>
<BR>
%s
<BR>
<INPUT TYPE='BUTTON' VALUE='Select Suite' onclick='onSuiteSelected();'>
</FORM>
</BODY>
</HTML>"""%(suitelist)

print htmlstring
