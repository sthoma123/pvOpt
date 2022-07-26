#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: ??????

# used to display usefull problem reports when reading and writing a datapoint.
# intended to be displayed to the advanced user.
# logs tuple: timestamp, thread, topic + message into globals.dplog dictionary (key is dp)
# limits number of entries to 1000 per datapoint
#  entrypoint: dpLog (dp, message)
#

print ("imported " + __name__)

import datetime
import config
import threading
import globals
import logging
import driverCommon
#----------------------------------------------------------------------
def getLead(): #returns tuple of timestamp and thread
        
    name=threading.currentThread().getName()
    timestamp= datetime.datetime.now()
    
    return [timestamp, name]

#----------------------------------------------------------------------
# copies buffer to globals dpLog
#
def flushLog(dp, buffer):
    if dp not in globals.dpLog:
        globals.dpLog[dp]=[]
    
    if isinstance(buffer, list):
        globals.dpLog[dp].extend(buffer)
        #limit size:
        MAXLOGSIZE=5000
        n = len(globals.dpLog[dp]) - MAXLOGSIZE
        if n>0:
            del (globals.dpLog[dp])[:n]
            
    else:
        logging.error ("dpLog got a wrong type %s as buffer:" % (str(type(buffer)), str(buffer)))
    
#----------------------------------------------------------------------
def get1Log(dp):    
    rv =[]
    if dp in globals.dpLog:
        rv = globals.dpLog[dp]
    else:
        s="<br>".join(globals.dpLog.keys())
        raise RuntimeError("dpLogger: no log data for %s, found: <br>%s" % (dp, str(s)))
    return rv
    
    
#----------------------------------------------------------------------
def getLog(dp):

    data  = [""]
    if type(dp) is list and len(dp) > 0:
        for d in dp:
            data.extend(get1Log(d))
        
    else:
        data = get1Log(dp)    
        
        
    rv={"info": driverCommon.getInfoArchive(dp),
        "header": ["timestamp", "thread", "topic", "message"], 
        "data":data}
    
    
    return rv
#----------------------------------------------------------------------
def log (buffer, topic, message): #timestamp, threadid, topic, message  stored in buffer


    #print ("dpLogger.log this is the message: %s" % str(message))
    
    if buffer == None:
        buffer=[]
        
    if isinstance(message, str):
        l=getLead()
        l.extend((topic, message))
        buffer.append(l)
    else:
        logging.error ("dpLog got a wrong type %s as message:" % (str(type(message)), str(message)))
    
    return buffer


#---------------------------------------------------------------------------------------
if __name__ == "__main__":

    with config.configClass() as configuration:
        globals.config = configuration
        logging.getLogger().setLevel(logging.DEBUG)
        
        if True:
            dp = "TASMOTA/MamaLampe/POWER@raspi"
            topic = "JUSTTESTING"
            buffer=[]
            
            log(buffer, topic, "das ist eine interessante testmessage")
            log(buffer, topic, "das ist noch eine interessante testmessage")            
            flushLog(dp, buffer)
            
            buffer=[]
            log(buffer, topic, "und die dritte das ist noch eine interessante testmessage")            
            flushLog(dp, buffer)
            
            print ("dpLogger: globals.dpLog contains \n %s" % str (globals.dpLog))


