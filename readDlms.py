#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
print ("imported " + __name__)

import os, glob, time, sys, datetime, socket
import globals
import cache
import config
from funcLog import logged
import logging
import dlms

import dpLogger

class Box:
    pass

__m = Box()  # m will contain all module-level values
__m.logBuffer = []


try:
    import cosemDecode
except Exception as e:
    logging.error("unable to load cosemDecode module on this box (%s): %s" % (socket.gethostname(), str(type(e))))
    pass
    
import helpers
    
import configparser
# Achtung: da die Abfrage des Zaehlers sehr lange dauert, arbeite ich _nur_ ueber den Cache.
# der Cache wird "freilaufend" gefuellt, ueber einen extra Thread refreshCache der im Server gestartet wird.
# wenn noch nichts im cache ist, wird es wie ein Fehler behandelt (und "?" als unit zurueckgeliefert statt "~")
#


#----------------------------------------------------------------------------------------------------
# returns complete dictionary of all available parameter in form dictionary of list[2]
#
@logged(logging.DEBUG)
def read_dlms_raw(serialPort):
    global __m
    #logging.error("read_dlms_raw: cache called read_dlms_raw  %s - %s" % (serialPort, str(globals.cache.autoRefreshfn.keys())))
    
    #foo = dlms.dlms(serialPort)
    foo = cosemDecode.cosem(serialPort)
    
    a=foo.tryQuery(__m.logBuffer)

    #logging.error("read_dlms_raw: calling close")
    foo.close()
    #logging.error("read_dlms_raw: cache exit read_dlms_raw  %s - %s" % (serialPort, str(globals.cache.autoRefreshfn.keys())))

    return a

#----------------------------------------------------------------------------------------------------
# returns rubbish, used if cache empty.
#
@logged(logging.DEBUG)
def read_dlms_nothing(zaehler):
    rv = dict()
    rv["Reason"]="noData"
    return rv    
    
#----------------------------------------------------------------------------------------------------
#
#  
#
@logged(logging.DEBUG)
def tryToMakeFloat(value):
    rv = value
    try:
        rv = float(value)
    except:
        pass
    
    return rv    
    
#----------------------------------------------------------------------------------------------------
#a function that checks that the connection was good and strips out the temperature
# zaehler ist der serielle Anschluss (ttyUSB0 oder ttyUSB1)
#
#

@logged(logging.DEBUG)
def read_dlms(zaehler, parameter): 
    global __m

    rv= None
    desc = dlms.OBISTranslate(parameter, globals.OBISconfig)  # was passiert bei falschen parameter?
    response={}
    try:
        #globals.cache.registerRefresh(zaehler, read_dlms_raw, 1) #refresh every second by cache itself!
        #response = globals.cache.get(zaehler, read_dlms_nothing, 86400) #24h
        response = globals.cache.get(zaehler, read_dlms_raw, 5) #
        value=tryToMakeFloat(response[parameter][0])
                
        rv = (desc + " (" + parameter + ")", 
              value, #value
              response[parameter][1], #unit
              datetime.datetime.fromtimestamp(globals.cache.getStamp(zaehler)),
              "DLMS/" + zaehler + "/" + parameter,
              "Ok"
              )
        
    except Exception as e:
        reason = ""
        if "Reason" in response.keys():
            reason=response["Reason"]
            unit="?"

        s="read_dlms %s, %s got error %s, reason %s " % (zaehler, parameter, str(e), reason)
        dpLogger.log(__m.logBuffer, "Exception", s)
        logging.exception(s)
        helpers.printError(s)
         
        unit = "~"
        reason = "Exception"
        
            
        #rv= zaehler+"/"+parameter, 0, unit , datetime.datetime.now(), zaehler+"/"+parameter
        rv = (desc + " (" + parameter + ")", 
              0, #value
              unit, #unit
              datetime.datetime.now(),
              "DLMS/" + zaehler + "/" + parameter,
              reason
              )
              
    return rv    

#----------------------------------------------------------------------------------------------------
# read takes defined datapoint syntax:
# takes list or string: /1.2.1/SUBID/SUBSUBID
# returns list: Name, Value, Unit, timestamp
@logged(logging.DEBUG)
def read(dp):
    global __m

    rv = None
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    while len(dpList) < 2:  # brauche zuminest 2 elemente, auch wenn sie leer sind!
        dpList += [""]
        
    if dpList[1] == "":
       dpList[1] = "1.7.0"
       
    rv = read_dlms(dpList[0], dpList[1])
    
    dpLogger.flushLog("DLMS/%s" %(dp), __m.logBuffer)
    __m.logBuffer = []
    
    return rv

#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:

    OBISconfig = configparser.ConfigParser()
    OBISconfig.read('/etc/obis.ini')

    globals.config= configuration
    if globals.cache is None:
        globals.cache = cache.CachedDict()
        
    parameterlist = "1.7.0", "2.7.0", "2.8.0", "1.8.0"
    while 1:
      for parameter in parameterlist:
        pp = read_dlms("ttyUSB.irKopf", parameter) 
        
        try:
            s=pp[0] + ": " + str(pp[1]) + " " + pp[2] + " " + str(pp[3]) + " " + str(pp[5])
            desc = pp[4]
            
            print (desc, s)
        except  Exception as e:
            print ('main: exception got wrong response from read_dlms_main')
            rv  ="main: Exception %s" % (type(e).__name__)
            rv += str(e)
            print (rv)
            print (pp)

      time.sleep(10)

