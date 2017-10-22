#!/usr/bin/python3
#
# timer modul wird von server.py gestartet, 
      
import os, time, datetime, sys, datetime, threading
import readETH008 as eth008
import readPV as PV
import readtemp as temp
import config
import logging
import globals
import driverCommon
import json
from funcLog import logged

globals.shutdown = False

#--------------------------------------------------------------------------------
#
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def getTimerDatapoints(name):
    rv = list()
    co=globals.config.__dict__
    dps=""
    k=globals.hostName + "/timer"
    #print ("getTimerDatapoints: search in .ini file: ", k)
    if k in co:
        #print ("getTimerDatapoints: found ", k)
        if name in co[k]: # found my timer:
            dpsString = co[k][name]
            rv = dpsString.split(",")

    print ("getTimerDatapoints: returned list: ", rv)

    return rv        

#--------------------------------------------------------------------------------
#
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def getTimertriggers(name):
    triggers=dict() #hier die triggerskriterien aus pvOpt.ini einlesen:
    
    co=globals.config.__dict__
    #liste alles was in pvopt.ini mit timer/anfaengt:
    k="timer/" + name
    for trigger in co[k]:
        triggers[trigger]=co[k][trigger]
        
    print ("getTimerTrigers returned ", triggers)
    return triggers
    
#--------------------------------------------------------------------------------
#
#  gibt die sekunden zurueck bis dass der naechste timer ablaeuft.
# achtung, erst wenn die Rueckgabe 0 oder <0 wird getriggert.
# bei dynamischen ausloesern weiss ich ja im vorhinein nicht wann es soweit ist.
#
#
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def gettimeToNextTrigger(triggers, lastRun):
    now = datetime.datetime.now()
    rv = 999999999
    for trigger in triggers.keys():
        timeTo = rv
        if trigger == "seconds":            
            timeTo = (lastRun - now).total_seconds() + int(triggers[trigger])
        elif trigger == "minutes":            
            timeTo = (lastRun - now).total_seconds() + 60 * int(triggers[trigger])
        elif trigger == "hours":            
            timeTo = (lastRun - now).total_seconds() + 3600 * int(triggers[trigger])
        elif trigger == "timestring":
            lasttimstr=lastRun.strftime(triggers[trigger])
            newtimstr=now.strftime(triggers[trigger])
            if lasttimstr == newtimstr:
                timeTo=60  # just a hint to the next check. since I want to stay flexible, don't calculate anything...
        else:
            raise ValueError('gettimeToNextTrigger timer %s unknown' % trigger)
            
        if timeTo < rv:
            rv = timeTo
        
    return rv
    
    
#--------------------------------------------------------------------------------
#
#  liest alle datenpunkte in der Liste damit diese ins Archiv kommen.
#
#
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def executeTimer(dpList):

    for dp in dpList:
        logging.debug("pvTimer.executeTimer read %s" % dp)
        driverCommon.read(dp, 0)
   
#--------------------------------------------------------------------------------
#
#  implementiert einen Timer
#  achtung: ist eine Threadfunktion, dahernur lokale Variablen veraendern!
#
#
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def timerFunc(name):

    print ("Timer ", name, " started")
    lastRun = datetime.datetime.fromtimestamp(0)  # hier die letzte laufzeit aus der VAR/timer/name einlesen, damit ich sauber restarten kann!
    triggers = getTimertriggers(name)
    dpList   = getTimerDatapoints(name)
    while (not globals.shutdown):
        sleepTime = gettimeToNextTrigger(triggers, lastRun)
        if sleepTime > 0:
            time.sleep(sleepTime)
        else:
            lastRun= datetime.datetime.now()
            executeTimer(dpList)


#--------------------------------------------------------------------------------
#
# startet die Timerthreads
#
#
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def pvTimerSetUp(dummy):
    try:            
        #better let only 1 timer run at the same time
        globals.timerLock=0
        #start a thread for every timer:
        timerNameList=list()
        
        co=globals.config.__dict__
        #liste alles was in pvopt.ini mit timer/anfaengt:
        for key in co.keys():
            s = key.split("/")
            if s[0] == "timer":
                timerNameList.append(s[1])
        
        print ("pvTimer got timers: " , timerNameList)
        
        timerThreadList=list()
        for threadNames in timerNameList:
            t = threading.Thread(target=timerFunc, args = (threadNames, ), name=threadNames)
            #t.setName=threadNames
            t.daemon = True
            t.start()       
            timerThreadList.append(t)
        
        # handle shutdown:
        while (not globals.shutdown):
            time.sleep(10)
            #check ob noch alle listenerthreads laufen, sonst shutdown!
            for t in timerThreadList:
                if not t.is_alive():
                    logging.error("  Timerthread %s stopped" % t.name)                        
                    print ("  Timerserver: Timerthread %s stopped - stopping myself" % t.name)                        
                    globals.shutdown = True
                        
        for t in timerThreadList: # 5 sec warten bis alle tot sind (server.py wartet laenger! auf mich)
            t.join(5.0)

    
    except  Exception as e:
        logging.exception("pvTimerSetUp")
        print("pvTimerSetUp Exception %s, %s" % (type(e).__name__, e.args))

#-------------------------------------------------------------------------
#
#
if __name__ == "__main__":
    with config.configClass() as configuration:
        globals.config= configuration   
        print ("pvTimer: start - with - debug")
        
        #logging.basicConfig(filename=globals.config.logfilename,level=logging.DEBUG, format='%(asctime)s--%(name)s--%(levelname)s--%(message)s')        
        #logging.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
                
        t2 = threading.Thread(target=pvTimerSetUp, args = (0, ))
        t2.daemon = True
        t2.start()

        while (not shutdown):
            time.sleep (10)
            