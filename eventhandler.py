#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
print ("imported " + __name__)
#
#der eventhandler verwaltet/verteilt alle events (read-events etc.)
#bekommt alle events von drivercommon und listeners ueber eine (1) queue
#
#  interface to this module:
#       enqueue(eventItem)       event ist ausgelöst
#       registerHandler(callback, infoDict, type, dp =None, value=None):  # acccepts regex as dp and value
#                                             retourniert index (handle)
#       unregister(index)         callback wird gelöscht
#       
#
#  interne functions:
#        flow()                   ruft callbacks auf, rules
#        transform()              transformiert z.B. einen Leistungssprung
#
#
# basis fuer die MQTT kommunikation
# aufteilung, vereinfachung von events (leistungsspruenge konfigurierbar in lesbare events)
#
#
# static        context.steps=[  #wird 1x beim startup aufgerufen, initialisiert, definiert functions etc.
#                   250,250,1500,1500
#
#               function a
#
#
# eventThread hat eigenschaften:
#
#   Name        AdjustWarmWasser
#   Trigger     onTimer("MinuteTimer") # d.h. hier nur oder erlaubt "Und macht keinen Sinn, da nix gleichzeitig ist)
#                                       #oder vom warmwassertimer ausgelöst
#   Action:     bilanz=context("Strom0") - context("Strom1") #python snippet, wird direkt ausgeführt, gibt ein paar mustache parms.
#               if bilanz > 0:
#                   increaseEigenverbrauch(bilanz)
#               else
#                   decrease Eigenverbrauch(bilanz)
#                   

#   Name        WarmWasser
#   Trigger     onReadEvent("MOD/ttyUSB.modbus/([01])/ZAEHLER/SystemPower")   #regEx variablen mit dp.0, dp.1 anzusprechen.
#   filter      True
#   ActionListOk  context(Strom{{dp.0}})=value
#                 context(error{{dp.0}})=False
#
#   ActionListException context(error{{dp.0}})=True
#                 TriggerEvent("AdjustWarmWasser")
#   
#                
#
#
#
#
# Eventengine: Feature description
#   every datapoint change goes thru event engine. With an "on_xxx" statement 
#       the respective action (list of conditions and writes) is triggered.
#       e.g. on_READEvent("PV/PV[01]")  filter für datenpunkt
#
#   if value <> 123 -> condition for next statments
#   if otherdatapoint.value 123 -> condition
#   and/or/not/xor -> condition
#   
#   action: 
#       onError (exception value from read or write)
#       context.value = 1234 += 123 -> python code?
#       context.mydatapointvalue = datapoint.read("adflkjfdslkj")
#       datapoint.write("adf")
#       trggerEvent (type, pause, 

#           
# --> welche code snippets: conditions, Actions, special functions (easy to extend!!!)
# --> metadefinition von python sourcecoede.
#
#
import os, glob, time,  sys, datetime, re

import select
import struct
import socket    # used for TCP/IP communication
import globals
import config
import logging
import cache
import metadata
from funcLog import logged
import socketserver
import queue
import threading
import argparse

import helpers


READEvent = 0
WRITEEvent = 1
EXTEvent = 2  #like update of subscription from mqtt, button pressed from eth boards, usually via ip request
TIMEREvent = 3  #periodische oder einmalige

eventTypeText = ( 
   "Read Event", "Write Event", "External Event", "Timer Event")
class event():
    def __init__(self, type, dp, value, srcTime=None):
        self.type = type
        self.dp = dp
        self.value = value     
        if srcTime is None:
            srcTime = datetime.datetime.now()
        self.srcTime = srcTime
        
        print("event constructor: %s" % (str(dp)))
        
    def __str__(self):
        return ("(class event: %s, dp \"%s\" val \"%s\" at %s)" % (eventTypeText[self.type], self.dp, self.value, str(self.srcTime)))
        
#----------------------------------------------------------------------------------------------------
#//wird von den workers aufgerufen
#stellt alles prinzipiell nur in die queue.
# dp ist ein gueltiger datenpunkt
# type ist ein typeOfEventEnum
# value ist direkt der Wert (nicht die Liste aus den read-funktionen)
# srcTime: wenn von der eventquelle geliefert wird, sonst wird now draus gemacht.
#
def enqueue(type, dp, value, srcTime=None):
#mache eventclass aus dem event

    globals.eventQueue.put(event(type, dp, value, srcTime))
    return 0
   
#----------------------------------------------------------------------------------------------------
#if there is an event, all registered handlers will be called.
# infoDict is a paramter that will be forwarded to the callback, it is used to pass parameters from the configuration (.ini) to the callback

globals.registeredCallbacks={}
def registerHandler(callback, infoDict, type, dp =None, value=None):  # acccepts regex as dp and value
    if type not in globals.registeredCallbacks:
        globals.registeredCallbacks[type] = {}  #list of dps
        
    if dp not in globals.registeredCallbacks[type]:  #None is a valid index in a dict.
        globals.registeredCallbacks[type][dp] = {}
        
    if value not in globals.registeredCallbacks[type][dp]:  #None is a valid index in a dict.
        globals.registeredCallbacks[type][dp][value] = [] #list of callbacks
    
    rv = len(globals.registeredCallbacks[type][dp][value]) # to be able to unregister callback later on.
    globals.registeredCallbacks[type][dp][value].append((callback, infoDict))

    return rv
#----------------------------------------------------------------------------------------------------
#  
def unRegisterHandler(index, type, dp = None, value = None):
    
    rv = False
    if type in globals.registeredCallbacks:
        if dp in globals.registeredCallbacks[type]:
            if value in globals.registeredCallbacks[type][dp]:
                callbacks = globals.registeredCallbacks[type][dp][value]
                if len(callbacks) > index:
                    callbacks[index]=None   # do not delete since the remaining indices would be invalidated.
                    rv = True
                
    return rv
                
#
def transform(eventItem, context):
    return eventItem
    
#----------------------------------------------------------------------------------------------------
#  
def regexMatch(reg, source):

    cnt = 0
    try:
        p = re.compile(reg)
        m = p.match(source)
        if m:
            cnt = 1

    except re.error:
        s = "eventhandler invalid regular expression %s ." % (str(reg))
        logging.exception(s)
        print (s)

            
    return source, cnt

#----------------------------------------------------------------------------------------------------
#  
def matchList(expression, list):  # returns set of matched items in given list  
#probably a performance impact: cache this operation?
    print ("matchList ex: %s, list: %s" % (str(expression), str(list)))
    
    rv =set()
    #if None in list:
    #    rv.add(None) # none matched immer
        
    #if expression in list:
    #    rv.add(expression)
        
    for x in list:
        if x is None:
            rv.add(None) # none matched immer
        elif x == expression: # exact match:
            rv.add(expression)
        else:
            print("regEx: ex: %s, match: %s" % (expression, str(x)))
            match, cnt = regexMatch(expression, x)
            if cnt > 0:
                rv.add(x)
        
    return rv
#----------------------------------------------------------------------------------------------------
#  
#
def flow(eventItem, context):
    #check for abonments, individual flows
    assert type(eventItem) is event and type(context) is dict, "flow expected class event as eventItem and dict as context. Got types: %s, %s " % (str(type(eventItem)), str(type(context)))
    
    print ("flow got eventItem %s " % str(eventItem))

    #registeredCallbacks is indexed several times:
    #    globals.registeredCallbacks[type][dp][value].append((callback, infoDict)
    
    #import web_pdb; web_pdb.set_trace() #debugging
    
    if eventItem.type in globals.registeredCallbacks:        
        matchedListDp = matchList(eventItem.dp, globals.registeredCallbacks[eventItem.type].keys())
        print ("flow matchList returned %s " % str(matchedListDp))
        if len(matchedListDp) > 0:
            print("flow: matched list %s " % str(matchedListDp))            
            for matchedDp in matchedListDp:
                matchedListVal = matchList(eventItem.value, globals.registeredCallbacks[eventItem.type][matchedDp].keys())
                print ("flow matchList Val returned %s " % str(matchedListVal))
                if len(matchedListVal) > 0:
                    print("flow: matched list %s " % str(matchedListVal))            
                    for matchedVal in matchedListVal:
                        try:
                            matchedVal[0](context, matchedVal[0], eventItem.type, eventItem.dp, eventItem.value) #call callback
                        except Exception as e:
                            s="eventhandler during callback  %s: Exception:  %s" % (str(eventItem), str(e))
                            logging.exception(s)
                            print (s)

    return eventItem;

#----------------------------------------------------------------------------------------------------
# worker:
# wird als thread gestartet,
# liest aus der Queue
#

globals.eventQueue = queue.Queue()
def worker(dummy):
    
    context={} #vielleicht mach ich den einmal persistent! da kann sich jedes Event (dp) die Vergangenheit merken.

    while (not globals.shutdown):
        try:
            eventItem = globals.eventQueue.get(True, 1) 
            print ("worker: Eventhandler got eventItem %s" % str(eventItem))
            #import web_pdb; web_pdb.set_trace() #debugging
            eventItem = transform(eventItem, context) # dort wird z.b. ein Leistungssprung auf ein spezifisches Geraet transformiert (mit context damit ich ein bisschen mitteln kann, bei mehreren messwerten)
            if eventItem is not None:
                eventItem = flow(eventItem, context)
            
        except queue.Empty: # timeout is not an error
            pass

    #globals.eventQueue.task_done()

#----------------------------------------------------------------------------------------------------
# cli:
#
#
def cli():
    """Start via command line interface."""
    parser = argparse.ArgumentParser(
        description="tests events and event workflow")
    workflow="{}"
    try:
        eventConfig = globals.config.configMap["event"]    
        if "workflow" in eventConfig:
            workflow=eventConfig["workflow"]
    except:
        pass
        
    print ("workflow %s" % workflow)
    
    parser.add_argument("-w", "--workflow", 
                        type=str, default = workflow,
                        help= "workflow (in JSON)")

    args = parser.parse_args()

    if all(arg in (False, None, "") for arg in (args.workflow)):
        parser.print_help()
    
    return (args.workflow)


        
#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main() :
  
  with config.configClass() as configuration:
    globals.config= configuration
    globals.shutdown = False
    

    workflow = cli() #cli needs config.
    
    workerThread = threading.Thread(target=worker, args = (None, ), name="Eventhandler_Worker")
    workerThread.daemon = True
    workerThread.start()

    while 1:
        if True:
            print ("got workflow %s"%(workflow))
            #def testCallBack(eventItem, context):
            def testCallBack(context, type, dp, value):
                
                if dp in context:
                    context[dp]=context[dp]-1
                else:
                    context[dp] = 10
                    
                print ("%d testcallback called with %d, %s, %s " % (context[dp], type, dp, value))
                return True
            
            dp = "HILFE/MY/OWN/DATAPOINT"
            index = registerHandler(testCallBack, {"info":"OWNRegex"}, READEvent, ".*\/OWN\/.*")
            index = registerHandler(testCallBack, {"info":"OWNRegex"}, READEvent, ".*\/MY\/.*")
            index = registerHandler(testCallBack, {"info":"OWNRegex"}, READEvent, ".*//OWN//.*") # wrong regular expression
            for x in range(1,5):
                enqueue(READEvent, dp, "that's the Value %d"%(x))
            
            time.sleep(10)
            #time.sleep(1000)
                
            print ("")
            break
            
                
                
if __name__ == '__main__':
    config.doNotParseCommandline = True

    main()

