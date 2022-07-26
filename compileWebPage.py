#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
print ("imported " + __name__)

"""
#
#  compileWebPage compiles the webpage from the user definition
#  in the config and the template files into the user or site specific
#  html files.
#  öäüÖÄÜß
#
#
"""


import os, glob, time, sys, datetime
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged
from funcLog import timeit
import metadata
import collections
import re
import copy
import JSONHelper


import threading
from threading import current_thread
threadLocal = threading.local()

import string
import random
# from https://pythontips.com/2013/07/28/generating-a-random-string/
def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


    
def localLog(s):
    threadLocal.printBuffer.append(s)
    print("localLog: %s" % s)

TYPE_UNKNOWN = -1
TYPE_ROOT = 0
TYPE_ASSIGNMENT = 1
TYPE_VARIABLE = 2
#hier die non-terminals
TYPE_PARMLIST = 100
TYPE_PARMENTRY = 101


class statement(object):
    def __init__(self, text= "", type=TYPE_UNKNOWN):
        self.m_terminalStatement = False
        self.m_type = type
        self.m_text = ""
        self.m_from=0
        self.m_to=0
        if type >= 100:
            m_terminalStatement = False
        
        
#----------------------------------------------------------

def read(dp):
    
    return rv

#------------------------------------------------------------------------------
#

def assure_path_exists(path):
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
                os.makedirs(dir)

#------------------------------------------------------------------------------
#
# write content to file (in folder)
#
#

def write2File(filename, content, depth):
    rv = ""
    fp = ""
    #search for template in subdir "templates"
    try:
        path= globals.config.configMap["wwwPath"]
        fp = path + filename
        assure_path_exists(fp) #"/".join(fp.split("/")[0:-1]))
        if type(content) is bytes:
            file = open(fp, 'wb')
        else:
            file = open(fp, 'w')
            

        file.write (content)
        s= " "*depth + filename + " <- (" + ", ".join(threadLocal.currContent) + ")"
        localLog(s)
        threadLocal.currContent=[]
        file.close()
        
    except Exception as e:
        s= " "*depth + " except: " + filename + " <- (" + ", ".join(threadLocal.currContent) + ")"
        localLog(s)
        threadLocal.currContent=[]
        logging.exception ("try to write to file %s " % fp)
        localLog("unable to write to %s" % fp)

    
    return rv
    
#
#------------------------------------------------------------------------------
#
# read content from file (in search in www/site/ and base folder)
#
#

def openTemplateFile(filename, mod=""):
    #search for template in subdir "templates"
    
    rv = None
    paths= [globals.config.configMap["wwwPath"], 
            globals.config.configMap["sitePath"] + "www/", 
            globals.config.configMap["basePath"] + "www/"]
    
    colors = ['<font class="text-info">', '<font class="text-warning">', '<font class="text-success">']
    nColors= ['</font>','</font>','</font>']
    i=0
    for path in paths:
        fp = path + filename
        #print ("Try to open %s " % fp)
        
        try:
            if mod=="":
                rv = open(fp, mode='r', encoding='utf-8', errors="replace") 
            else:
                rv = open(fp, mode='r'+mod) 
            if rv is not None:
                #localLog("read from %s (%s)" % (fp, str(threadLocal.currContent)))
                threadLocal.currContent.append(colors[i]+filename+nColors[i])
                break
                
        except OSError as e:
            #print ("not found %s " % fp)
            i += 1
            rv = None
            pass
            
        except Exception as e:
            logging.exception("openTemplateFile exception for %s " % fp)
            rv = None

    #print ("result  %s " %(  str(rv)))
    if rv is None:
        s="cannot open file %s in paths: %s" %(filename, " or ".join(paths))
        localLog(s)
        logging.error(s) 

    return rv
    
#-------------------------------------------------------------------------------
# replace slashes by "_" for html-IDs.
#
#
def  modifyID(content):
    return content.replace("/", "_").replace(".", "_")
    
    
#-------------------------------------------------------------------------------
# parmModifier are extensions to datapoints that are separated by "."
# they specify a specific function to be applied to the datapoint.
#
#
#

def modifyParm(modifier, content):
    #assert type(fullParm) is str, "modifyParm: expect fullparm as string ($$xxx.ID$$, got %s" % str(parms)
    # could be dict as well
    # achtung: wenn content auch eine Variable ist, dann muss der modifier weitergereicht werden, da er nur auf das endziel angewendet werden darf
    
    rv = content
    try:
            if "" == modifier:
                pass
            elif "$$" == content[0:2] and "$$" == content[-2:]: #weiterreichen
                rv = content[0:-2] + "." + modifier + "$$"
            elif "ID" == modifier:
                rv = modifyID(content)
            elif "ENCODE" == modifier:
                rv = JSONHelper.encodeParm(content)
            else:
                #unknown modifier:
                rv = "modifyParm %s unknown modifier: for %s" % [modifier, content]
    except:
        pass
        
    return rv

#------------------------------------------------------------------------------
# translate1Parm handles datapoint reads etc.
# if a parm content start with "@", the function defined after the @ is executed
# returns string, kann aber auch liste sein (wenn für forEach)
# liste nun automatisch sortiert.
# returns empty string if error.

def translate1Parm(p, addParms):
    assert type(p) is str, "translate1Parm expects string got %s " % (str(type(p)))
    rv = p
    if len(p)> 0 and p[0] == "@":
        # resolve variables
        #import web_pdb; web_pdb.set_trace() #debugging
        pt = substituteParms(p, addParms, [], "translate1Parm %s " % (p))

        pp=pt.split("@")
        box=pp[2]
        dp = pp[1]
        
        #import web_pdb; web_pdb.set_trace() #debugging
        localLog("startReading %s@%s" % (dp, box))
        #d = driverCommon.readViaWeb(dp = dp, target = box, maxAge = 999999)  //read data only from cache.
        d = driverCommon.readViaWeb(dp = dp, target = box, maxAge = 5000) #cached data is Ok...
        localLog("finished reading %s@%s, got %s" % (dp, box, str(d)))
        
        rv = "" #case of error:
        if (type(d) not in [tuple, list]): #error
            localLog("Warning1: read DP %s@%s. %s" % (dp, box, str(d)))
        else:
            if len(d) < 5 or d[5] != "Ok":
                localLog("Warning2: read DP %s@%s. %s %s" % (dp, box, str(d[0]), str(d[5])))
            else:
                rv=d[1]
                if type(rv) is float:
                    rv = "%0.8s %s" % (d[1], d[2])

    return rv
    
# translateParm kann auch liste kriegen

def translateParm(p, addParms):

    rv = p

    if type(p) is str:
        rv = translate1Parm(p, addParms)
    elif type(p) in (tuple, list):
        rv = []
        for pp in p:
            rv.append(translate1Parm(pp, addParms))
    else:
        assert True, "translateParm expects string or list got %s " % (str(type(p)))

    #liefert string oder liste...
    return rv

#------------------------------------------------------------------------------

def handle1parm(rv, pp, dictOfParms):
    p=pp.replace("$$","")
    modifier=""
    pl = p.split(".")
    
    if len(pl)> 1:
        p=pl[0]
        modifier = pl[1]
        

    #print ("handle1parm: parm is %s modifier is %s" % (p, modifier))

    if "$$"+p+"$$" in dictOfParms:
        ss = dictOfParms["$$"+p+"$$"]
        s = modifyParm(modifier, ss)
        #print ("replace %s by %s " % (pp, s))
        if type(s) in [list, dict]:
            s = str(s)
            
        rv=rv.replace(pp, s)
    
    return rv
#------------------------------------------------------------------------------
#
#
#

def resolveDefaultsParms(parmList, parms):

    rv = dict()
    i=0
    for p in parmList:
        s=""
        if i<len(parms) and parms[i] is not None:
            s=parms[i]
        else:
            s=p[1]    #default
        logging.debug ("replace %s by %s" % (p[0], s))
        #rv = rv.replace(p[0],s)
        rv[p[0]]=s
        i=i+1
        
    return rv

            
def substituteParmsOnce(rv, dictOfParms, fn): # helper for substituteParms (no recursive check)
        
    usedParms=parseFileContent(rv, fn)
        
    #print("parameters for %s are %s " %(fn, str(dictOfParms)))
    
    #only handle every parm once
    setOfUsedParms = set(usedParms)
    
    #substitute and check for modifiers:
    for p in setOfUsedParms:
        rv = handle1parm(rv, p, dictOfParms)

    return rv

#------------------------------------------------------------------------------
# templ: content of file
# parmList: list of 2-element-list [[inputparmname, default]] or dict 
# parms: list of content, matches with parmlist.
#

def substituteParms(templ, parmList, parms, fn):
    assert type(parms) is list, "substituteParms: expect parms as list of strings, got %s" % str(parms)
    assert type(parmList) in [list, dict], "substituteParms: expect parmList as list of 2-element list or dict, got %s" % str(parmList)
    
    rv = templ
    
    dictOfParms = dict()
    #import web_pdb; web_pdb.set_trace() #debugging
    if type(parmList) is list:
        dictOfParms=resolveDefaultsParms(parmList, parms)
    else:
        dictOfParms = parmList
        
    #import web_pdb; web_pdb.set_trace() #debugging
        
    #ersteinmal referenzen innerhalb von Parms auflösen, damit modifier im Dokument auf die entgültigen inhalte losgehen!
    for p in dictOfParms.keys():
        # das riecht nach einer schönen rekursion!, daher keine Loop?
        if type(dictOfParms[p]) is str: # nur für strings! (allenfalls könnte ich dicts und lists nach JSONIFyen
            dictOfParms[p] =  substituteParmsOnce(dictOfParms[p], dictOfParms, "%s of %s" % (p,fn))
    
    while True:
        last = rv
        rv = substituteParmsOnce(rv, dictOfParms, fn)
        if last == rv: # sonst nochmal fuer rekursive verweise!
            break
    return rv


Token = collections.namedtuple('Token', ['typ', 'value', 'line', 'column'])

def tokenize(code, token_specification, fn):
    keywords = {'parm', 'IF', 'THEN', 'ENDIF', 'FOR', 'NEXT', 'GOSUB', 'RETURN'}
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    line_num = 1
    line_start = 0
    #if fn == "templates/inputBoxTable.html":
    #    print("tokenize start %s" %tok_regex)

    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group(kind)
        #if fn == "templates/inputBoxTable.html":
        #    print("tokenize found %s, %s " % (kind,value))

        if kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
        elif kind == 'SKIP':
            pass
        elif kind == 'MISMATCH':
            raise RuntimeError('{fn!r}: {value!r} unexpected on line {line_num}'.format(fn = fn, value=value, line_num=line_num))
        else:
            if kind == 'ID' and value in keywords:
                kind = value
            column = mo.start() - line_start
            yield Token(kind, value, line_num, column)



#------------------------------------------------------------------------------
# returns list of statements
#
#

def parse1(label, source, syntax):

    statements=list()
    prefix = ""
    postfix = source
    
    while postfix != "":  #loop ueber kompletten rest
        if label in syntax:
            sy=syntax[label]

            prefix, sm, postfix = myMatch(postfix, sy)
            if len(prefix) > 0:
                logging.warning("ignored %s in %s " % (prefix, source))
                
            if sm.m_terminalStatement:
                statements.append(sm)
            else:
                s = parse1(sy[2], sm.m_text, syntax)
                if type(s) is list and len(s) > 0:
                    statements.extend(s)
        else:
            logging.error ("mySyntaxError while interpreting %s" % source)
   
    return statements
    
#------------------------------------------------------------------------------
#
def myTrim(what, s):
    rv = s
    l = len(what)
    if len(s)>l:
        if rv[0:l] == what:
            rv = rv[l:]
        if rv[-1*l:] == what:
            rv = rv[0:-1*l]
    return rv
    
#------------------------------------------------------------------------------
#
# returns list of parameternames 
#
#

def interpreteHeaderTokens(tokenList, currToken, fn):
    rv = None
    context = "" # START, PARM, ID, EQUAL, OPER, STOP
    try:
        while currToken < len(tokenList):
            t = tokenList[currToken]
            currToken += 1
            
            #print ("interprete Token: context is %s, token found %s " % (context, t.typ))
            
            if t.typ == "STOP": #stop ist der einzige legale ausweg, egal wo.
                context = ""
                if rv is None or len(rv) == 0: #ist auch ein Fehler: keine parms gefunden!
                    s= "%s: no valid parms found stop , got <%s> in line %s: %s" % (fn, t.value, t.line, t.column)
                    print (s)
                    raise RuntimeError(s)
                else:
                    break

            elif context == "": # jetzt warte ich auf start, alles andere ist aber kein Fehler.
                if t.typ == "START":
                    context = "START"
                    
            elif context == "START": # jetzt muss parm kommen, zukuenfigt auch etwas anderes also kein Fehler
                if t.typ == "parm":
                    context = "parm"  # der beginn einer parameterdefinition
                    rv = list()
                 
            elif context == "parm":  #nach parm muss ID kommen, sonst fehler!
                if t.typ == "ID":
                    context = "ID"
                    #print ("append to rv %s"%t.value)
                    rv.append([t.value, ""]) #jeder parm besteht aus [value, default Liste]
                else:
                    s= "%s: syntax error: expect ID after parm, got %s in line %s: %s" % (fn, t.value, t.line, t.column)
                    #print (s)
                    raise RuntimeError(s)
            
            elif context == "ID": #jetzt darf gleich ein listsep kommen oder ein assigment
                if t.typ == "LISTSEP":
                    context = "parm"  #ich bin bereit fuer neuen parm
                elif t.typ == "EQUAL" or t.typ=="ASSIGN":  #momentan noch kein unterschied!
                    context = "EQUAL"
                else:
                    s= "%s: syntax error: expect LISTSEP or EQUAL after parm, got %s in line %s: %s" % (fn, t.value, t.line, t.column)
                    #print (s)
                    raise RuntimeError(s)
                    
            elif context == "EQUAL":
                if t.typ == "LISTSEP":
                    context = "parm"  #ich bin bereit fuer neuen parm
                elif t.typ == "LITERAL":
                    #print ("append default LITERAL to rv %s"%t.value)
                    rv[-1][1] += myTrim('"', t.value)
                elif t.typ == "ID":
                    #print ("append default ID to rv %s"%t.value)
                    rv[-1][1] +=  t.value
                elif t.typ == "NUMBER":  #number is treated the same as literals (converted to string)
                    rv[-1][1] +=  str(t.value)
                elif t.typ == "OP":
                    #bleibe im assigment, unterscheide nicht zwischen operatoren.
                    pass
                else:
                    s= "%s: syntax error: expect LITERAL, ID or OPERATOR or LISTSEP after ASSIGNMENT, got %s : %s in line %s: %s" % (fn, t.typ, t.value, t.line, t.column)
                    #print (s)
                    raise RuntimeError(s)
            else:
                s= "%s: syntax error: unhandled Context: %s  got %s in line %s: %s" % (fn, context, t.value, t.line, t.column)
                #print (s)
                raise RuntimeError(s)

    except Exception as e:
        logging.exception("compileWebPage.py - interpreteHeaderTokens")
        rv = None

    return rv

#------------------------------------------------------------------------------
#
# returns list of parameternames 
# separated by $$xx$$
# simple version: schneller!
#

def parseFileContent(content, fn):
    parmList=list()
    tokenList=list()
    rv = list()
    try:
        c = content.split("$$")
        i=1
        while i < len(c):
            rv.append("$$" + c[i] + "$$")
            i = i + 2
            
    except Exception as e:  #ist eigentlich kein fehler, da das file offenbar keine parameterzeile hat: nur loggen:
        s="parseFileContent %s unable find parameters %s : %s" % (fn, type(e).__name__, str(e))
        localLog (s)
        #logging.exception("tokenize and interpreteHeaderTokens ")
        rv = None
    
    return rv

#------------------------------------------------------------------------------
#
# returns list of parameternames separated by $$xx$$
#
#

def parseFileHeader(header, fn):

    token_specification = [
        ('START', r'<!--'),
        ('STOP', r'-->'),
        ('LITERAL', r'\"[^\"]*\"'), #literals koennen alles enthalten...
        ('NUMBER', r'\d+(\.\d*)?'), # Integer or decimal number
        ('ASSIGN', r':='), # Assignment operator
        ('EQUAL', r'='), # Equal operator
        ('END', r';'), # Statement terminator
        ('LISTSEP', r','), # Statement terminator
        ('ID', r'[$A-Za-z]+[0-9$]*'), # Identifiers
        ('OP', r'[+\-*/]'), # Arithmetic operators
        ('NEWLINE', r'\n'), # Line endings
        ('SKIP', r'[ \t\.]+'), # Skip over spaces and tabs
        ('MISMATCH',r'.'), # Any other character
    ]

    parmList=list()
    tokenList=list()
    rv=None
    try:
        for token in tokenize(header, token_specification, fn):
            #print(token)
            tokenList.append(token)
        currToken=0
        #retourniert etwas in der form:
        #    [[["$$parm1", ""],["$$parm2", "defaultforparm2"]]
        rv = interpreteHeaderTokens(tokenList, currToken, fn)
    except Exception as e:  #ist eigentlich kein fehler, da das file offenbar keine parameterzeile hat: nur loggen:
        s="%s unable to tokenize %s : %s, ignoring first line" % (fn, type(e).__name__, str(e))
        localLog (s)
        print (header)
        print (s)
        
        #logging.exception("tokenize and interpreteHeaderTokens ")
        rv = None
    
    return rv

#
#------------------------------------------------------------------------------
#
#
#
def handle1BinObject(templ, depth, compPath):

    rv = None
    fileBin = openTemplateFile(templ,"b")
    if fileBin  != None:
        rv = fileBin.read()  #read binary, sonst gibts bei .min. oder .css files probleme mit der UTF-8 umwandlung...
        fileBin.close()
    
    return rv
#
#------------------------------------------------------------------------------
#
# write content to file (in folder)
#
#

def handle1Object(templ, parms, depth, compPath, addParms={}):
    rv = None
    try:
        if parms is None:
            rv=handle1BinObject(templ, depth, compPath) #just copy
        else:
            with openTemplateFile(templ) as fh:
                s=fh.readline()
                parmList = parseFileHeader(s, templ)
                if parmList is None: #erste Zeile enhaelt nichtmal parm tag muss wohl html code sein -> just copy
                    threadLocal.currContent.pop(); # ignore first try to open this file.
                    rv = handle1BinObject(templ, depth, compPath).decode('utf-8') # binobject returns binary
                else:
                    rv = fh.read()  #read remainder
                    if rv != None:
                        parmList.append(["$$compPath$$", compPath])
                        parmList.append(["$$base$$", templ])
                        parmList.append(["$$uniqueID$$", random_generator(6, string.ascii_letters)])
                        for x in addParms.keys():
                            parmList.append([x, addParms[x]])
                        #import web_pdb; web_pdb.set_trace() #debugging
                        rv = substituteParms(rv, parmList, parms, templ)
                fh.close()

    except Exception as e:
        #rv = "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now(), dp, "Exception"
        logging.exception("compileWebPage.py in %s" % compPath)
        
    return rv
    
#----------------------------------------------------------------------------------------------------
# handleDict handles one class/object
# liefert "" bei fehler zurueck
#

def handleDict(d, depth, compPath, addParms={}):  
    rv =""
    base=""
    target=""
    parms=None
    forEach=[""]
    forEachVar="$$tally$$"
    forEachSorted = 0
    
    if "forEach" in d:
        fe = d["forEach"]
        if type(fe) is list:
            forEach =fe
        elif type(fe) is dict:
            if "content" in fe:
                forEach=translateParm(fe["content"], addParms)
            if "var" in fe:
                forEachVar = fe["var"]
            if "sorted" in fe:
                forEachSorted = fe["sorted"]
        else:
            localLog("Warning: unknown ForEachType %s in %s, should be list or dict with content and var" % (str(type(fe)), compPath))
            
    if "base" in d:
        base = d["base"]
    if "target" in d:
        target = d["target"]
    if "parms" in d:
        parms = d["parms"]  #wenns parm garnicht gibt, dann wird nur umkopiert, sonst wird wenigstens die parmliste im file evaluiert.
    if "forEachVar" in d:
        forEachVar = d["forEachVar"]
        
    if base == "":
        logging.error("no baseclass for %s " % str(d))
        #import web_pdb; web_pdb.set_trace() #debugging

    else:
        #parms sollte liste von strings sein. wenn statt eines strings ein dict oder liste ist, muss er interpretiert werden.
        assert parms is None or type(parms) is list, "parameter %s should be a list" % str(parms)
        if forEachSorted != 0:
            #import web_pdb; web_pdb.set_trace() #debugging
            forEach = sorted(forEach, reverse = False if forEachSorted==1 else True)
        
        for x in forEach:
            addParms["$$base$$"] = base
            addParms["$$compPath$$"] = compPath
            addParms[forEachVar]=x
            workingParms=copy.deepcopy(parms)
            
            if type(workingParms) is list: # otherwise just copy
                for i in range(0,len(workingParms)):
                    workingParms[i] = translateParm(workingParms[i],addParms)
                    if type(workingParms[i]) is dict:
                        #localLog("handleDict: to next level workingParms[i] is not a str (its a %s)" %(str(type(workingParms[i]))))
                        workingParms[i]=compileWebPage(workingParms[i], depth+1, compPath + "#parms#%d" %(i), addParms)

            if type(base) is not str: # i was ned ob des ned a bledsinn is: .............................................
                #localLog("handleDict: to next level base is not a str (its a %s)" %(str(type(base))))
                base=compileWebPage(base, depth+1, compPath+"/base", addParms)
                #
            s=handle1Object(base, workingParms, depth, compPath, addParms)  # could be bytes.
            if len(rv) > 0:
                rv = rv + s
            else:
                rv = s
            
            if rv is None:
                #print ("Handle1Object returned None for baseclass %s" % base)
                rv = ""
            else:
                if target != "": # andernfalls fileinhalt zurueckgegebn und weiterverwenden.
                    #target kann auch variabel sein (configpages!)
                    t = substituteParms(target, addParms, [], "targetFileName %s " % (target))
                    write2File(t, rv, depth)
                    rv = ""
        
    return rv

#----------------------------------------------------------------------------------------------------
# compileWebPage: makes everything
#    calls itself recursively 
#    returns output (string), if there is no target
#

def compileWebPage(d, depth, compPath, addParms={}):

    rv=""
    if type(d) is list:
        i=0
        for item in d:
            rv += compileWebPage(item, depth+1, compPath+"#%s" %(str(i)), addParms)
            i=i+1
    elif type(d) is dict:
        # in handledict werden parms ersetzt, daher uebergebe ich eine Kopie, 
        rv += handleDict(copy.deepcopy(d), depth, compPath, addParms)  
    elif type(d) is str:
        rv += d
    elif type(d) is int:
        rv += "%d" % (d)
    else:
        s="Error: compileWebPage got unknown type: (%s)" % (str(type(d)))
        localLog(s)
        logging.Error(s)
        
    return rv


#----------------------------------------------------------------------------------------------------
# compile:
#    wrapper for compileWebPage, to map rv
#    returns information to be presented to the user.
#    note: this concept relies on a single-thread call.
#

@timeit
def compileWP(what):

    threadLocal.printBuffer = []
    threadLocal.currContent = [] #helper for current target

    localLog("start-compile for %s" % (what))

    d= globals.config.configMap["compile"][what]
    addParms={}
    
    s=compileWebPage(d, 0, what,addParms)
    
        
    return threadLocal.printBuffer
    
    
#----------------------------------------------------------------------------------------------------
# MAIN:
#

#-------------------------------------------------------------------------
#
#
def main():
    
    current_thread.name= "myMainThread"
    logging.getLogger().setLevel(logging.DEBUG) #default for standalone usage
    ll = logging.getLevelName(logging.getLogger().level)
    #//print ("default log level is %s " %(ll))
    
    with config.configClass() as configuration:
        globals.config= configuration   
        print ("compileWebPage: start - with -l debug")
        
        ll = logging.getLevelName(logging.getLogger().level)
        print ("current log level is %s " %(ll))
        
        yy= [
            {"forEach": { "content": "@CONFIG@raspi4:8000", "var": "$$iniSection$$" },
             "base":"templates/inputBoxTable.html", "parms":[
                "CONFIG/$$iniSection$$", "raspi4", "$$iniSection$$", "updating..."
            ]}
            ]
            
        d=[
            { "target": "abstractMenuClass", "base":"templates/menuClass.html", "parms":
              [
                {"base":"templates/join.html", "parms":[
                    #{"base":"templates/menuItemClass.html", "parms":["HomeMatic"]},
                    {"base":"templates/menuItemClass.html", "parms":["Home"]},
                    {"base":"templates/menuItemClass.html", "parms":["Wohnzimmer"]},
                    {"base":"templates/menuItemClass.html", "parms":["Actions"]},
                    {"base":"templates/menuItemClass.html", "parms":["dpLog"]},                    
                    {"base":"templates/menuItemClass.html", "parms":["oben"]},                    
                    {"base":"templates/menuItemClass.html", "parms":["edda"]},                    
                    {"base":"templates/menuItemClass.html", "parms":["Tasmota"]},                    
                    {"base":"templates/menuItemClass.html", "parms":["BatterX"]},                    
                    {"base":"templates/menuItemClass.html", "parms":["Verteilung"]},                    
                    {"base":"templates/menuItemClass.html", "parms":["Eingang"]},                    
                    
                    #{"base":"templates/menuItemClass.html", "parms":["Kueche"]},
                    #{"base":"templates/menuItemClass.html", "parms":["PV"]},
                    #{"base":"templates/menuItemClass.html", "parms":["Garten"]},
                    #{"base":"templates/menuItemClass.html", "parms":["Technik"]},
                    #{"base":"templates/menuItemClass.html", "parms":["Zaehler"]},
                    #{"base":"templates/menuItemClass.html", "parms":["Schalter"]},
                    #{"base":"templates/menuItemClass.html", "parms":["Cams"]},
                    {"base":"templates/menuItemClassWithSub.html", "parms":["Config", None, "fa-wrench",
                        {"base":"templates/join.html", "parms":[
                            {"forEach": { "content": "@CONFIG@localhost:8000", "var": "$$iniSection$$" , "sorted" : 1 },
                             "base":"templates/menuItemClass.html", 
                             "parms":["$$iniSection$$"]}
                        ]}
                    ]}
                    ]
                }
              ]
           },
           { "target": "menuHomeMatic.html", "base":"abstractMenuClass", "parms": [ "HomeMatic" ]  },
           { "target": "menuHome.html", "base":"abstractMenuClass", "parms": [ "Home" ]  },
           { "target": "menuWohnzimmer.html", "base":"abstractMenuClass", "parms": [ "Wohnzimmer" ]  },
           { "target": "menuActions.html", "base":"abstractMenuClass", "parms": [ "Wohnzimmer" ]  },
           { "target": "menuKueche.html", "base":"abstractMenuClass", "parms": [ "Kueche" ]  },
           { "target": "menuPV.html", "base":"abstractMenuClass", "parms": [ "PV" ]  },
           { "target": "menuGarten.html", "base":"abstractMenuClass", "parms": [ "Garten" ]  },
           { "target": "menuTechnik.html", "base":"abstractMenuClass", "parms": [ "Technik" ]  },
           { "target": "menuZaehler.html", "base":"abstractMenuClass", "parms": [ "Zaehler" ]  },
           { "target": "menuSchalter.html", "base":"abstractMenuClass", "parms": [ "Schalter" ]  },
           { "target": "menuSchalter.html", "base":"abstractMenuClass", "parms": [ "Config" ]  },
           { "target": "menuCams.html", "base":"abstractMenuClass", "parms": [ "Cams" ]  },
           { "target": "menudpLog.html", "base":"abstractMenuClass", "parms": [ "dpLog" ]  },
           { "target": "menuOben.html", "base":"abstractMenuClass", "parms": [ "oben" ]  },
           { "target": "menuUnten.html", "base":"abstractMenuClass", "parms": [ "unten" ]  },
           { "target": "menuEdda.html", "base":"abstractMenuClass", "parms": [ "edda" ]  },
           { "target": "tasmota.html", "base":"abstractMenuClass", "parms": [ "Tasmota" ]  },
           
           
           { "forEach": { "content": "@CONFIG@localhost:8000", "var": "$$iniSection$$", "sorted" : 1 },
             "target": "$$iniSection.ID$$.html", "base":"templates/page.html", "parms": [ 
                {"base":"abstractMenuClass", "parms": [ "$$iniSection$$" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[ "Config / $$iniSection$$", 
                            {"base":"templates/dynamicDataDisplay.html", "parms":[
                                    "CONFIG/$$iniSection$$", "localhost", "$$iniSection$$", None, "rw"
                            ]},
                            "12"   # whole screen width
                    ]}
                ]},
                {"base":"templates/join.html", "parms":[
                    #{ "base":"templates/popup.html", "parms":["caption", "content" ] },
                    '<link href="./css/tree.css" rel="stylesheet">',
                    { "base":"templates/HTMLDataTemplates.html", "parms":[] },
                    { "base":"templates/HTMLDataTemplateTree.html", "parms":[] },
                    { "base":"templates/HTMLDataTemplateEditWebpage.html", "parms":[] }
                ]}
           ]},
           # page for Energiefluss
            { "target": "verteilung.html", "base":"templates/page.html", "parms": [ 
                {"base":"pages/menu.html", "parms": [ "Verteilung" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "PV",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1553", "raspi", "", "-", "ro"
                            ]}
                        ]}
                    ]}
                ]},
                {"base":"templates/join.html", "parms":[
                    #{ "base":"templates/popup.html", "parms":["caption", "content" ] },
                    '<link href="./css/tree.css" rel="stylesheet">',
                    { "base":"templates/HTMLDataTemplates.html", "parms":[] },
                    { "base":"templates/HTMLDataTemplateTree.html", "parms":[] },
                    { "base":"templates/HTMLDataTemplateEditWebpage.html", "parms":[] }
                ]}
            ]},
# page for BatterX
            { "target": "batterx.html", "base":"templates/page.html", "parms": [ 
                {"base":"pages/menu.html", "parms": [ "BatterX" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "PV",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1553", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1554", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1569", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1570", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1617", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1618", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1634", "raspi", "", "-", "ro", "", "2"
                            ]}
                        ]}
                    ]},
                    {"base":"templates/panel.html", "parms":[
                        "Battery",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1042", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1058", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1074", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/1121", "raspi", "", "-", "ro", "", "2"
                            ] }
                        ]}
                    ]},
                    {"base":"templates/panel.html", "parms":[
                        "State",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2321/1", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2321/2", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2321/3", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2321/4", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2337/1", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2337/2", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2337/3", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2337/4", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2465/1", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2465/2", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2465/3", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2465/4", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2465/5", "raspi", "", "-", "ro", "", "2"
                            ]}
                        ]}
                    ]},
                    
                    {"base":"templates/panel.html", "parms":[
                        "Grid",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2833", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2834", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2835", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2897", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2898", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2899", "raspi", "", "-", "ro", "", "2"
                            ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2913", "raspi", "", "-", "ro", "", "2"
                            ]}, 
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2897/2", "raspi", "", "-", "ro", "", "2"
                            ]},                            
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2898/2", "raspi", "", "-", "ro", "", "2"
                            ]},                            
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2899/2", "raspi", "", "-", "ro", "", "2"
                            ]},                            
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/2913/2", "raspi", "", "-", "ro", "", "2"
                            ]},                   
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/24582", "raspi", "", "-", "ro", "", "2"
                            ]},                  
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/28417", "raspi", "", "-", "ro", "", "2"
                            ]}                            
                        ]}
                    ]},
                            
                    {"base":"templates/panel.html", "parms":[
                        "Input",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/337", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/338", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/339", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/353", "raspi", "", "-", "ro", "", "2"
                            ] },
                            "<br>",
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/273", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/274", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/275", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/305", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/306", "raspi", "", "-", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "BX/BATTERX/307", "raspi", "", "-", "ro", "", "2"
                            ] }
                        ]}
                    ]}
                ]},
                {"base":"templates/join.html", "parms":[  #pageIncludes
                    { "base":"templates/popup.html", "parms":["caption", "content" ] },
                    { "base":"templates/HTMLDataTemplates.html", "parms":[] },
                    { "base":"templates/HTMLDataTemplateTree.html", "parms":[] }
                ]}
            ]},

# page for lower Floor
            { "target": "edda.html", "base":"templates/page.html", "parms": [ 
                {"base":"pages/menu.html", "parms": [ "edda" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "Eddazimmer",
                        {"base":"templates/join.html", "parms":[
                            {"base":"templates/onOffButton.html", "parms": [ "Licht Eddazimmer",
                            "HM/HMRASPI/MEQ0360043/1/STATE", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "Edda Strom Schreibtisch",
                            "TASMOTA/EddaStrom/POWER@raspi", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "Edda Strom Stehlampe",
                            "TASMOTA/EddaStehlampe/POWER@raspi", "raspi" ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HM/HMRASPI/OEQ1694613/4/ACTUAL_TEMPERATURE", "raspi", "", "Eddazimmer Temp", "ro", "", "2"  #
                            ]}                            
                        ]},
                        "12"
                    ]},
                    {"base":"templates/panel.html", "parms":[
                        "Bad",
                        {"base":"templates/join.html", "parms":[
                            "<p>",
                            {"base":"templates/onOffButton.html", "parms": [ "Licht Bad Kalt",
                            "HM/HMRASPI/OEQ2698103/1/LEVEL", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "Licht Bad Warm",
                            "HM/HMRASPI/OEQ2698191/1/LEVEL", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "Licht Bad Spiegel",
                            "HM/HMRASPI/MEQ0360960/1/STATE", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "Licht Kammerl",
                            "HM/HMRASPI/PEQ1196025/1/LEVEL", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "Licht Vorzimmer",
                            "HM/HMRASPI/MEQ0360937/1/STATE", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "Lichtstreifen Vorzimmer",
                            "TASMOTA/LichtVorzimmer/POWER@raspi", "raspi" ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HM/HMRASPI/OEQ1694602/4/ACTUAL_TEMPERATURE", "raspi", "", "Bad Temp", "ro", "", "2"  #
                            ]}   
                        ]},
                        "12"
                    ]}
                ]},
                {"base":"templates/join.html", "parms":[  #pageIncludes
                    { "base":"templates/popup.html", "parms":["caption", "content" ] },
                    { "base":"templates/HTMLDataTemplates.html", "parms":[] },
                    { "base":"templates/HTMLDataTemplateTree.html", "parms":[] }
                ]}
            ]},

# page for upper Floor
            { "target": "oben.html", "base":"templates/page.html", "parms": [ 
                {"base":"pages/menu.html", "parms": [ "oben" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "Schlafzimmer",
                        {"base":"templates/join.html", "parms":[
                            "<a href=\"http://192.168.0.44\">LichtSchlafzimmer</a><br>",
                            {"base":"templates/onOffButton.html", "parms": [ "Licht Schlafzimmer",
                            "TASMOTA/LichtSchlafzimmer/POWER1@raspi", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "Flur",
                            "HM/HMRASPI/MEQ0360937/1/STATE", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "SigiStrom",
                            "TASMOTA/SigiStrom/POWER@raspi", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "LichtVorzimmer",
                            "TASMOTA/LichtVorzimmer/POWER@raspi", "raspi" ]},
                            "<a href=\"http://192.168.0.44\">LichtSchlafzimmer</a>",
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HM/HMRASPI/OEQ1694573/4/ACTUAL_TEMPERATURE", "raspi", "", "Temp Schlafzimmer", "ro", "", "2"  #
                            ]},
                            "<br><a href=\"http://192.168.0.38\">DimmerVorzimmer</a>",
                            "<br><a href=\"http://192.168.0.49\">LichtVorzimmer</a>"
                        ]},
                        "12"
                    ]},
                    {"base":"templates/panel.html", "parms":[
                        "Sigizimmer",
                        {"base":"templates/join.html", "parms":[
                            "<p>",
                            {"base":"templates/onOffButton.html", "parms": [ "LichtSigi",
                            "TASMOTA/LichtSigi/POWER1@raspi", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "SigiStrom",
                            "TASMOTA/SigiStrom/POWER@raspi", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "StromUSV",
                            "TASMOTA/StromUSV/POWER@raspi", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "StromComputer",
                            "TASMOTA/StromComputer/POWER@raspi", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "StromSchreibtisch",
                            "TASMOTA/LichtSigi/POWER2@raspi", "raspi" ]},
                            {"base":"templates/onOffButton.html", "parms": [ "PrusaStrom",
                            "TASMOTA/PrusaStrom/POWER@raspi", "raspi" ]},
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                            "HM/HMRASPI/NEQ1489656/4/ACTUAL_TEMPERATURE", "raspi", "", "Temp SigiZimmer", "ro", "", "2"]},

                            "</p><br><a href=\"http://192.168.0.51\">Strom Computer</a>",
                            "<br><a href=\"http://192.168.0.32\">Strom Drucker</a>",
                            "<br><a href=\"http://192.168.0.50\">Strom USV</a>",                          
                            "<br><a href=\"http://192.168.0.43\">LichtSigi, StromSchreibtisch</a>",
                            "<br><a href=\"http://192.168.0.40\">SigiStrom</a>"
   
                        ]},
                        "12"
                    ]}
                ]},
                {"base":"templates/join.html", "parms":[  #pageIncludes
                    { "base":"templates/popup.html", "parms":["caption", "content" ] },
                    { "base":"templates/HTMLDataTemplates.html", "parms":[] },
                    { "base":"templates/HTMLDataTemplateTree.html", "parms":[] }
                ]}                
            ]},

# external Links für Tasmota
            { "target": "tasmota.html", "base":"templates/page.html", "parms": [ 
                {"base":"pages/menu.html", "parms": [ "tasmota" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "Tasmota devices",
                        {"base":"templates/join.html", "parms":[
                        "<a href=\"http://192.168.0.44\">LichtSchlafzimmer</a>",
                        "<br><a href=\"http://192.168.0.45\">LichtWaschkeller</a>",
                        "<br><a href=\"http://192.168.0.49\">LichtVorzimmer</a>",
                        "<br><a href=\"http://192.168.0.38\">DimmerVorzimmer</a>",
                        "<br><a href=\"http://192.168.0.41\">EddaStrom</a>",
                        "<br><a href=\"http://192.168.0.31\">MamaLampe</a>",
                        "<br><a href=\"http://192.168.0.42\">LichtHeizkeller</a>",                        
                        "<br><a href=\"http://192.168.0.52\">Strom Lader Keller</a>",
                        "<br><a href=\"http://192.168.0.51\">Strom Computer</a>",
                        "<br><a href=\"http://192.168.0.32\">Strom Drucker</a>",
                        "<br><a href=\"http://192.168.0.50\">Strom USV</a>",                          
                        "<br><a href=\"http://192.168.0.43\">LichtSigi</a>",
                        "<br><a href=\"http://192.168.0.40\">SigiStrom</a>"
                        "<br><a href=\"http://192.168.0.53\">Lichtaltegarage</a>"
                        "<br><a href=\"http://192.168.0.203\">Wasserzaehler</a>",
                        
                        "<br><br><a href=\"http://192.168.0.182\">Kellerschalter</a>",
                        "<br><a href=\"http://192.168.0.188/index.htm\">Keller2</a>",
                        "<br><a href=\"http://192.168.0.185\">wohnzimmer</a>",
                        "<br><a href=\"http://192.168.0.186\">kueche</a>",
                        
                        "<br><br><a href=\"http://192.168.0.8:4000\">teslamate</a>",
                        "<br><a href=\"http://192.168.0.8:3000\">teslamate grafana</a>",
                        
                        
                        ]},
                        "12"
                    ]}
                ]}
            ]},
# liste für dpLog
            { "target": "dpLog.html", "base":"templates/page.html", "parms": [ 
                #{"base":"abstractMenuClass", "parms": [ "dpLog" ]  },
                {"base":"pages/menu.html", "parms": [ "dpLog" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "Datapoint Log",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicList.html", "parms":[
                                "dp_from_CompileWebPage.py", "box", "", "dp - updating", "ro", "", "readLog"
                            ] }
                        ]},
                        "12"   # whole screen width
                    ]}
                ]}
            ]},
# liste für BXLog
            { "target": "BXLog.html", "base":"templates/page.html", "parms": [ 
                {"base":"pages/menu.html", "parms": [ "BXLog" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "BatterX Log",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicList.html", "parms":[
                                "BX/BATTERX/WARNINGS", "raspi", "", "dp - updating", "ro", "", "readMultiJ" #default method...
                            ] }
                        ]},
                        "12"   # whole screen width
                    ]}
                ]}
            ]},
           
            { "target": "Home.html", "base":"templates/page.html", "parms": [ 
                {"base":"abstractMenuClass", "parms": [ "Home" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "&Uuml;bersicht",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "TEMP/00042d9aabff", "kellerraspi", "", "Temperatur Draussen", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "TEMP/00042cb4d4ff", "kellerraspi", "", "Temperatur Wohnzimmer", "ro", "", "2"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HEALTH/UPTIME/K", "kellerraspi", "", "Uptime kellerraspi", "ro"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HEALTH/UPTIMESERVICE/K", "kellerraspi", "", "Uptime kellerraspi", "ro"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HEALTH/UPTIME/Z", "zaehlerraspi", "", "Uptime zaehlerraspi", "ro"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HEALTH/UPTIMESERVICE/Z", "zaehlerraspi", "", "Uptime zaehlerraspi", "ro"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HEALTH/UPTIME/R", "raspi", "", "Uptime raspi", "ro"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HEALTH/UPTIMESERVICE/R", "raspi", "", "Uptime raspi service", "ro"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HEALTH/UPTIME/R4", "raspi4", "", "Uptime raspi4", "ro"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "HEALTH/UPTIMESERVICE/R4", "raspi4", "", "Uptime raspi4 service", "ro"
                            ] }
                        ]}
                    ]},
                    {"base":"templates/panel.html", "parms":[
                        "PV",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "PV/PV0/PAC", "kellerraspi", "", "Leistung PV0", "ro", "", "0"
                            ] },
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "PV/PV1/PAC", "kellerraspi", "", "Leistung PV1", "ro", "string_template", "0"
                            ] }
                        ]}
                    ]}
                ]},
                {"base":"templates/join.html", "parms":[
                    { "base":"templates/popup.html", "parms":["caption", "content" ] },
                    { "base":"templates/HTMLDataTemplates.html", "parms":[] },
                    { "base":"templates/HTMLDataTemplateTree.html", "parms":[] }
                ]}
              ]},
              
           { "target": "index.html", "base":"Home.html", "parms": [ "" ]  },
           { "target": "Wohnzimmer.html", "base":"templates/page.html", "parms": [ 
                { "base":"abstractMenuClass", "parms": [ "Wohnzimmer" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "Licht",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/dynamicDataDisplay.html", "parms":[
                                "PV/PV0/PAC", "raspi", "", "PV0", "rw"
                            ] },
                            {"base":"templates/inputBoxTable.html", "parms":[
                                "HM/HMraspi/QEQ1842516/1/LEVEL", "raspi4", "Wohnzimmerlicht", "0-101"
                            ]},
                            
                            {"forEach": { "content": ["A", "B", "C"], "var": "$$tally$$" },
                             "base":"templates/join.html", "parms":[
                                 "$$tally$$", "@MOD/ttyUSB.modbus/14/SDM120/Power@zaehlerraspi:8000", "<br>"
                             ]
                            }
                        ]}
                    ]},
                    {"base":"templates/panel.html", "parms":[
                        "Aktueller Verbrauch",
                        {"base":"templates/dataPointLine.html", "parms":[
                            'MOD/ttyUSB.modbus/14/SDM120/Power', "zaehlerraspi:8000"
                        ]}
                    ]}
                ]}
              ]},
           { "target": "Actions.html", "base":"templates/page.html", "parms": [ 
                {"base":"abstractMenuClass", "parms": [ "Configuration" ]  },
                {"base":"templates/join.html", "parms":[
                    {"base":"templates/panel.html", "parms":[
                        "Webpage",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/execButton.html", "parms":[  #executiert eine prozedur am Server
                                "Compile Webpage", "compileWP", "webPageDefinition", "localhost"
                            ]}
                        ]}
                    ]},
                    {"base":"templates/panel.html", "parms":[
                        "Flush",
                        {"base":"templates/join.html", "parms":[
                            { "base":"templates/execButton.html", "parms":[  #executiert eine prozedur am Server
                                "flush Configuration", "flushConfig", "", "localhost"
                            ]}
                        ]}
                    ]}
                ]}
              ]},
           { "target": "JSONProxy.php", "base":"templates/JSONProxy.php", "parms": [ "raspi4"]  },
           { "target": "miniProxy.php", "base":"templates/miniProxy.php", "parms": [ "raspi4"]  }
        ]

        files = ["css/bootstrap.min.css", "css/bootstrap-slider.css", 
                 "css/font-awesome.min.css", "css/metisMenu.min.css",
                 "css/sb-admin-2.css", "css/mchp.css", "css/pvChart.css", "css/pvOpt.css",
                 "js/bootstrap.min.js", "js/diagAuswahl.js", "js/jquery.min.js", "js/metisMenu.min.js",
                 "js/moment-with-locales.min.js", "js/pvDiag.js", "js/pvOpt.js", "js/site.js", "js/sb-admin-2.js", "js/mchp.js",
                 "fonts/fontawesome-webfont.eot", "fonts/fontawesome-webfont.svg", "fonts/fontawesome-webfont.ttf",
                 "fonts/fontawesome-webfont.woff", "fonts/fontawesome-webfont.woff2", "fonts/FontAwesome.otf",
                 "js/bootstrap-slider.js", "test.php", "js/popup.js", "js/mustache.js", "css/popup.css", "css/tree.css",
                 "js/pnotify.custom.js", "css/pnotify.custom.css"
                 ]
        d.extend([ { "target": fn, "base":"templates/" + fn} for fn in files])
        
        configuration.writeConfig("compile", {"webPageDefinition" : d})
        #config.printDict(configuration.configMap, 0)

        #import web_pdb; web_pdb.set_trace() #debugging
        configuration.flushConfig()

        rv = compileWP("webPageDefinition")
        print("compileWP returned")
        for s in rv:
            print ("--- %s ---" % s)
        
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()
