#!/usr/bin/python3

THIS MODULE IS OBSOLETE, Tasmota is covered by transformation of MQTT commands.
#
#
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
#"""
#
#
#..write("
# def write(dp, value, pulse=None):
#
# registriert eine funktion, die aufgerufen wird, wenn sich etwas ändert.
# pollcycle optional 
# def callback (dp, value)
#  
# TAS is a small overlay module for MQTT.
# it ensures that I can write and read with the same datapoint to be able to use the normal button front-end.
# mapping from TASmota to MQTT:
# commands see: https://github.com/arendst/Sonoff-Tasmota/wiki/Commands
#
#   TAS/my_sonoff/power/1@broker 
#      -> write: cmnd/my_sonoff/
#      -> read /stat/my_sonoff/POWER1

#   TAS/XOR/my_sonoff/power/1@broker:
#      -> write cmnd/mySonoff/power1/TOGGLE
#      -> read cmnd/mySonoff/POWER1
#blink 
#
print ("imported " + __name__)
import os, glob, time, sys, datetime, queue
import threading
import argparse
import json
import config
import globals
from funcLog import logged
import logging
import metadata
import helpers
import readMQTT as MQTT

    
#----------------------------------------------------------------------------------------------------
# worker:
# hier werden inputs von TAS  behandelt:
# ????ich mache 2 threads, da der socket-server blockiert, und ich ihn ueberwachen bzw. bei 
# ???einem shutdown sauber runterfahren will.
#
#
#TASPORT = 17495  #zum testen
TASPORT = 1883  #
TASSPORT = 8883  #

        
#----------------------------------------------------------------------------
def worker(dummy):    
    while (not globals.shutdown):
        time.sleep(2) #???
        
#----------------------------------------------------------------------------
# returns transformed dp
def transformRead(dp) :
    rv = dp
    return rv

#----------------------------------------------------------------------------
# returns transformed value
def transformReadResult(dp, value):
    rv = (dp, value)
    return rv


#----------------------------------------------------------------------------
# returns transformed dp and value
def transformWrite(dp, value):
    rv = (dp, value)
    return rv



#----------------------------------------------------------------------------------------------------
# read_TAS called via cache
# converts datapoint and forwards it to MQTT
#----------------------------------------------------------------------------------------------------
#
@logged(logging.DEBUG)
def read_TAS(dp):
    
    rv = metadata.read("TAS/" + dp, "TAS/" + dp)    
    
    topic, broker = dp.split("@")
            
    try:
        pass
            
    except Exception as e:
        logging.exception ( "TAS: problem with %s" % (dp))
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "TAS/%s" %(dp), "Exception"
                    
    return rv    
        

#----------------------------------------------------------------------------------------------------
# read takes defined datapoint syntax:
# takes list or string: topic/subtopic/.../...@broker
# returns list: Name, Value, Unit, timestamp
def read(dp):

    rv = None

    l = dp.split("@")
    if len(l) < 2:
        broker = ""
        l.append(broker)  #default broker ist in MQTT konfiguriert.
        
    topic, broker = l[0:2]
    
    dp = topic +  "@" + broker        

    rv = globals.cache.get(dp, read_TAS, 0)  #hier über den cache zu gehen ist vermutlich etwas überspitzt;

    return rv

#----------------------------------------------------------------------------------------------------
# raw_write
#
#
#
def raw_write (dp, value, pulsetime):

    l = dp.split("@")
    if len(l) < 2:
        broker = ""
        l.append(broker) #default broker in MQTT
        
    topic, broker = l[0:2]
    dp = topic +  "@" + broker        

    rv = metadata.read("TAS/" + dp, "TAS/" + dp)    
    rv [1] = value
    rv [5] = "Ok"
    
    if pulsetime is None:
        pulsetime = 0
  
    try:
        mq = globals.TASClients[broker]  
        TASMessageInfo = mq["client"].publish(topic, payload=value, qos=0, retain=False)        
        if TASMessageInfo.rc != 0:
            s="TAS on_connect to %s with Status %d (%s)" % (broker, rc, TASReturnCode[rc])
            print (s)
            raise Exception(s)
                        
    except Exception as e:
        logging.exception ( "TAS:  problem with %s" % (dp))
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "TAS/%s" %(dp), "Exception"
                    
    return rv    


#----------------------------------------------------------------------------------------------------
# write:
#   publishes a TAS value
#
@logged(logging.DEBUG)
def write(dp, value, pulsetime=None):  #3rd parameter needed for some other providers...

    try:
        
        if type(dp) is str:
            dpList=dp.split('/')
        else:
            dpList=dp
            
        if len(dpList) > 1:        
            i=0
            if dpList[i]=="XOR":
                # convert to "TOGGLE"
                i=i+1
                dp = "/".join(dpList[i:])
                value = "TOGGLE"
                    
            globals.cache.invalidate(dp)
            rv = raw_write(dp, value, pulsetime)

    except Exception as e:
        logging.exception ( "writeTAS problem with %s" % (dp))
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "TAS/%s" %(dp), "Exception"

    return rv

#----------------------------------------------------------------------------------------------------
def cli():
    """Start via command line interface."""
    parser = argparse.ArgumentParser(
        description="tests TAS brokers subscribes to given topic, publish test topic"
                    "  topic/subtopic/../../..@broker, wildcards are # and +")
    broker="loalhost"
    try:
        TASConfig = globals.config.configMap["TAS"]    
        if "broker" in TASConfig:
            broker=TASConfig["broker"]
    except:
        pass
        
    print ("default broker %s" % broker)
    
    parser.add_argument("-d", "--dp", metavar='Datapoint',
                        type=str, default = "#@" + broker,  #default broker defined in .ini file.
                        help="datapoint in the form topic/subtopic/../../..[@broker]")
                        
    parser.add_argument("-v", "--value", 
                        type=str, default = "",
                        help="value for publishing topic")

    parser.add_argument("-p", "--pulse", 
                        type=str, default = 0,
                        help="pulsetime in seconds (if supported)")

    parser.add_argument("-q", "--quality", 
                        type=str, default = 0,
                        help= "QoS: At most once (0), At least once (1), Exactly once (2).")

    parser.add_argument("-b", "--broker", 
                        type=str, default = broker,
                        help= "broker, TAS server")

    args = parser.parse_args()

    if all(arg in (False, None, "") for arg in (args.dp)):
        parser.print_help()
    
    return (args.dp, args.value, args.pulse, args.quality, args.broker)

    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main() :

  config.doNotParseCommandline = True  
  
  with config.configClass() as configuration:
    globals.config= configuration
    globals.shutdown = False

    dp, value, pulse, quality, broker = cli() #cli needs config.
    
    workerThread = threading.Thread(target=worker, args = (None, ), name="TASserver_Worker")
    workerThread.daemon = True
    workerThread.start()

    while 1:
        if False:
            print ("got %s, %s, %s, %s, %s"%(dp, value, pulse, quality, broker))
            if -1 == dp.find("@"):
                fullDP = dp + "@" + broker
            else:
                fullDP = dp 
                
            print ("")
            if value != "":
                print("write %s returns " % fullDP, write(fullDP, value, pulse))
            else:
                print("read %s returns " % fullDP, read(fullDP))
            print ("")
            
        for i in range(1,5):
            print (".")
            time.sleep(2)
            dp = "tele/MamaLampe/LWT@raspi"
            print("read %s returns " % dp, read(dp))
            dp= "prusa/temperature/tool0"
            print("read %s returns " % dp, read(dp))            
            dp= "prusa/temperature/schnuckiputzi"
            print("read %s returns " % dp, read(dp))            
        break

    globals.shutdown = True
    
    workerThread.join(10)
    
    if workerThread.isAlive():  
        print ("workerthread still alive ")
    else:
        print ("workerthread finished")

if __name__ == '__main__':
    config.doNotParseCommandline = True
    print ("readTAS set donot to True")

    main()

