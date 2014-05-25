#!/usr/bin/env python 
import cgi, cgitb
print "Content-Type: text/html\n"     # HTML is following
cgitb.enable()
form = cgi.FieldStorage()
suts = form.getlist('sutid')
bench = form.getvalue('bedname')


from CCommunicator import CCommunicator
web =CCommunicator('webclient')
import time
timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
webid   = 'webid'+timestamp
casename= 'cs'+timestamp

sutlines ='<table border="0" width="100%" >\n<tr class="noborders">\n'
if len(suts)!=0:
    width= 100/len(suts)
width =100
gsuts = str(suts)   
goutput = ""
selecttag = ""
fisrt = True
selected = "selected='selected' "
for sut in  suts:
    if fisrt !=True:
        selected =''
    selecttag = selecttag + "<option %s >%s</option>"%(selected ,sut)
    output = '"%s":"",'%sut
    goutput= goutput+output
    line = """<td><p>SUT:%s</p><br><textarea id='"""%sut+sut+"""' style='width:"""+str(width)+"""%' rows=40 name='"""+sut+"""' value=''></textarea></td>"""
    sutlines =sutlines + line
if goutput[len(goutput)-1]==',':
    goutput=goutput[:len(goutput)-1]
sutlines="<p>Bench: %s</p>"%bench+sutlines+"</tr></table>"
htmlstring ='''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <script type="text/javascript">
    <!--
    var sut1Timer=0;
    var gPause=0 ;
    var gStart=0 ;
    var gEndCase = 0;
    var gSut1Output="hello world";
    var suts = '''+gsuts+''';
    var gsutoutput= {'''+goutput+'''};
    var gcaseoutput=''
        function post( id, dest, params )
        {
            var xmlhttp;

            if (window.XMLHttpRequest)
            {// code for IE7+, Firefox, Chrome, Opera, Safari
                xmlhttp=new XMLHttpRequest();
            }
            else
            {// code for IE6, IE5
                xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
            }

            xmlhttp.onreadystatechange=function()
            {
                if (xmlhttp.readyState==4 && xmlhttp.status==200)
                {
            
            if (id =="case_output"){
                gcaseoutput=gcaseoutput+xmlhttp.responseText;
                var caseoutput   = document.getElementById( "case_output" );
                caseoutput.innerHTML =gcaseoutput
                caseoutput.value=gcaseoutput
                caseoutput.scrollTop =    caseoutput.scrollHeight;
            }
            else{
            gsutoutput[id]= gsutoutput[id] + xmlhttp.responseText;
            }
        }    
             
                return xmlhttp.responseText;

        }
            xmlhttp.open("POST",dest,true);
            xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
            xmlhttp.send( params ); 
            return ""
        }


        function onSutUpdateRequest()
        {
    
            for ( var i=0 ; i < suts.length ; ++i ){ 
                var id = suts[i]
                var response ="";
                response = post( id,"/cgi-bin/myCGI2.py", "WEBSESSIONID="+encodeURI("'''+webid+'''")+"&CASENAME="+encodeURI("'''+casename+'''")+"&SUTNAME="+encodeURI(id) );            
                gsutoutput[id]= gsutoutput[id] + response;            
                if (gPause==0)
                {
                    var output   = document.getElementById( id );
                    output.innerHTML = gsutoutput[id];
                    output.value= gsutoutput[id];
                    output.scrollTop =    output.scrollHeight;
                }
            }
            if (gEndCase !=1) {setTimeout("onSutUpdateRequest()",300); }
            
        }

    function onPauseSutUpdate()
        {
        gPause=1;
    }

    function onResumeSutUpdate()
        {
        gPause=0;
        if (gStart==0)
        {
            gStart=1;
            onSutUpdateRequest();            
        }    
    }




    function onCaseCommand(cmd, expect,waittime)
    {
        var response ="";
        var cmd   = document.getElementById( "area2" );
        if (cmd.value==""){ return ""}
        //alert(cmd.value)
        response = post( "case_output","/cgi-bin/webCmd2server.py", "WEBSESSIONID="+encodeURI("'''+webid+'''")+"&CASENAME="+encodeURI("'''+casename+'''")+"&COMMAND="+encodeURI(cmd.value)+"&EXPECT="+encodeURI(".")+"&WAITTIME="+encodeURI(1) );
        cmd.innerHTML =response;
        //o=o+response
        cmd.value =response;

        
        caseoutput   = document.getElementById( "case_output" );
        caseoutput.innerHTML =gcaseoutput
        caseoutput.value=gcaseoutput
        caseoutput.scrollTop =    caseoutput.scrollHeight;
    }

    function onSUTCommand(cmd, expect,waittime)
    {
        var selectedSut = document.getElementById("sutnamelist")
        var sutname = selectedSut.options[selectedSut.selectedIndex].value
        var response ="";
        var cmd   = document.getElementById( "SUTCMD" );
        if (cmd.value==""){ return ""}
        //alert(cmd.value)
        response = post( "case_output","/cgi-bin/webCmd2server.py", "WEBSESSIONID="+encodeURI("'''+webid+'''")+"&CASENAME="+encodeURI("'''+casename+'''")+"&COMMAND="+encodeURI(cmd.value)+"&EXPECT="+encodeURI(".")+"&WAITTIME="+encodeURI(1)+"&SUTNAME="+encodeURI(sutname) );
        cmd.innerHTML =response;
        //o=o+response
        cmd.value =response;

        
        caseoutput   = document.getElementById( "case_output" );
        caseoutput.innerHTML =gcaseoutput
        caseoutput.value=gcaseoutput
        caseoutput.scrollTop =    caseoutput.scrollHeight;
    }
    
        function onEndCase()
    {
        response = post( "case_output","/cgi-bin/webCmd2server.py", "WEBSESSIONID="+encodeURI("'''+webid+'''")+"&CASENAME="+encodeURI("'''+casename+'''")+"&COMMAND="+encodeURI("set caseresult end")+"&EXPECT="+encodeURI(".")+"&WAITTIME="+encodeURI(1) );
        gEndCase=1
    }
    -->
    </script>
</head>

<body onload="onResumeSutUpdate();"><p></p><table border="0" width="100%" >
<tr class="noborders">'''+sutlines+'''
<form name="f1" onsubmit="onCaseCommand(); return false;" autocomplete="on"> 
<p>Command: <input id="area2" name="COMMAND" type="text" value="ls" rows="1" size="100%" autocomplete="on">  
  <input name="go" value="ENTER" type="button" onClick="onCaseCommand();"></p>
</form>
<form name="f2" onsubmit="onSUTCommand(); return false;" autocomplete="on"> 
<p>SUT: <select name="SUTNAMELIST" id="sutnamelist" value="1"> '''+selecttag+'''</select> 
    <input id="SUTCMD" name="SUTCOMMAND" type="text" value="ls" rows="1" size="100%"  autocomplete="on">  
  <input name="go" value="ENTER" type="button" onClick="onSUTCommand();"></p>
</form>
  <div id="textarea2" type="text"></div>

    <textarea id="case_output" style="width:100%" rows=6 name="review" value="aaaaaaaaaa">Short review</textarea>
    <p id="case_output1" row=6>  </p>
    <input value="Start" type="button" onClick="onResumeSutUpdate();">
    <input value="Pause" type="button" onClick="onPauseSutUpdate();">

    <input value="EndCase" type="button" onClick="onEndCase();">
</body>

</html>
'''
print htmlstring

import StringIO,csv
io =StringIO.StringIO()
wt =csv.writer(io)
#print 'bench:',bench
#print 'suts:',suts
suts.insert(0, bench)
benchsuts = suts
#print benchsuts
wt.writerow(benchsuts)
cmd =io.getvalue()
cmd = 'manualruncase '+cmd
rsp= web.TxWEB2SERVER_CONTROL_COMMAND_UPDATE(webid, casename,cmd)


#===============================================================================
#     <input value="SutCommand" type="button" onClick="onSutCommand();">
# 
# 
#    <a href="javascript:onCaseCommand()">Case Command</a>  
#     <a href="javascript:onSutCommand()">SUT Command</a><br>
# 
#<input id="scriptBox" type="text" onkeypress="onCaseCommand();" />
# 
# <input type="file" id="files" name="files[]" multiple />
# <output id="list"></output>
#===============================================================================

