#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
#
# todo: use dpLoger to be more verbose.
#
#
#
#
#"""
#
#
#..write("
# def write(dp, value, pulse=None):
#
# registriert eine funktion, die aufgerufen wird, wenn sich etwas ändert.
# pollcycle optional 
# def register(dp, threshhold = 0, pollcycle = 0, callback) 
# def callback (dp, value)
#
# in drivercommon wird register auf einen pollcycle gemapped wenn es kein "register" im read-modul gibt
# der callback führt die in den rules aufgelisteten aktionen durch
# rules sind über eine drag/drop oberfläche zu konfigurieren (siehe node-red, The runtime is built on Node.js. The flows created in Node-RED are stored using JSON.)
#  
#
#
#
print ("imported " + __name__)

import os, glob, time, sys, datetime
import threading
#import http, http.client
import argparse
import json
import config
import paho.mqtt.client as mqttClient

import globals
from funcLog import logged
import logging
import metadata
import queue
import eventhandler
import helpers



#initialize my globals (no good style to do it in globals module)
try:
    dummy = globals.mqttClients
except:
    globals.mqttClients = {}

    
#----------------------------------------------------------------------------------------------------
# worker:
# hier werden inputs von MQTT  behandelt:
# ????ich mache 2 threads, da der socket-server blockiert, und ich ihn ueberwachen bzw. bei 
# ???einem shutdown sauber runterfahren will.
#
#
#MQTTPORT = 17495  #zum testen
MQTTPORT = 1883  #
MQTTSPORT = 8883  #

        
def worker(dummy):
    
    while (not globals.shutdown):
        time.sleep(2) #???
        
    # go thru list of mqtt clients to disconnect and stop them all.
    try:
        for broker in globals.mqttClients:
            client=globals.mqttClients[broker]["client"]
            print("Stopping MQTT client " + str(client._client_id))
            client.disconnect()
            client.loop_stop()
            
    except Exception as e:
        s="MQTTServer: Exception while stopping mqttclients %s" % (str(e))
        logging.exception(s)
        print(s)
        pass
    
#----------------------------------------------------------------------------------------------------
# [MQTT_raspi]
# subscribe=JSON:["tele/+/LWT", "prusa/mqtt"]
def getListOfdefaultSubscriptions(broker):
    rv = ""
    
    try:
        mqttConfig = globals.config.configMap["MQTT_" + broker]
        if "subscribe" in mqttConfig:
            rv=mqttConfig["subscribe"]
    except:
        pass
        
    return rv
    
#----------------------------------------------------------------------------------------------------
# waits for message and subscribe if there is a message. 
# stops with disconnect
# reads toSubscribeQueue and exectutes commands.
#
def subscriptionThread (broker):
    print ("subscriptionThread for %s started" % broker)
    
    mq = globals.mqttClients[broker]
    client = mq["client"]    
    brokerDisconnected=False
    
    try:
        while not brokerDisconnected and not globals.shutdown:  #and connection disconnected
            try:                            
                topic = mq["toSubscribeQueue"].get(True, 1) 
                if topic == "brokerDisconnectedEvent":
                    brokerDisconnected = True
                else:
                    client.subscribe(topic)
                    mq["subscriptions"].add(topic) # ist ein set, kein dict
                    print("subscriptionthread: %s subscribed topic %s " % (broker, topic))                
            except queue.Empty:
                pass
                  
    except Exception as e:
        #just a timeout; ignore
        s="readMQTT subscriptionThread %s: Exception:  %s" % (broker, str(e))
        logging.exception(s)
        print (s)
                                     
    print ("subscriptionThread for %s stopped" % broker)
#----------------------------------------------------------------------------------------------------
# server auf port:
#returns mqttClient.Client object
# or None.
#
MQTTReturnCode = [
    "Connection successful",
    "Connection refused – incorrect protocol version",
    "Connection refused – invalid client identif,ier"
    "Connection refused – server unavailable",
    "Connection refused – bad username or password",
    "Connection refused – not authorised",
    ]
    
def start_MQTTclient(port, broker, clientName):

    client = None
    #import web_pdb; web_pdb.set_trace() #debugging
    
    try:
    
        def on_connect(client, userdata, flags, rc):
            try:
                if rc==0:
                    print ("hooray connecctteedd")
                    mq = globals.mqttClients[broker]                    

                    subscriptions=getListOfdefaultSubscriptions(broker)
                    for sub in subscriptions:
                        print ("enqueued %s default Subscription" % sub)
                        mq["toSubscribeQueue"].put(sub)
                        
                    #start subscriptionthread
                    th = threading.Thread(target=subscriptionThread , args = (broker, ), name="MQTT subscription for %s" % broker)
                    th.daemon = True
                    th.start()
                    mq["subscriptionThread"] = th
                                            
                    #(result, mid)=client.subscribe(subscriptions)
                    # start subscriptionthread:
                    
                else:
                    #print ("mqtt: on_connect connect rc returned %d != 0" % rc);
                    s="MQTT on_connect to %s with Status %d (%s)" % (broker, rc, MQTTReturnCode[rc])
                    print (s)
                    raise Exception(s)
                    
            except Exception as e:
                s="readMQTT on_connect %s: problem:  %s" % (broker, str(e))
                logging.exception(s)
                print (s)

        def on_message(client, userdata, msg):
            try:
                topic = msg.topic
                mq = globals.mqttClients[broker]
                #this topic is obviousely subscribed:
                mq["subscriptions"].add(topic)
                payload = msg.payload
                if isinstance(payload, bytes): # converty to string (actually datatype is not defined in mqtt)
                   payload = payload.decode('utf-8')
                   
                logging.error("NotAnError: got mqtt message topic <%s> payload <%s> @ <%s>"%(topic, payload, broker))

                fullDp="MQTT/"+topic+"@"+broker
                rv=globals.cache.getValue(fullDp)  #just to get unit and metadata text
                if rv is None:
                    rv=[fullDp, payload, "~", datetime.datetime.now(), fullDp, "Ok"]
                rv[1]=payload
                rv[3]=datetime.datetime.now()
                rv[5]="Ok"
                print("MQTT on_message for %s: %s = %s" % (fullDp, topic, str(payload)))
                globals.cache.enterValue(fullDp, rv,10)
                eventhandler.enqueue(eventhandler.EXTEvent, fullDp, payload)

            except Exception as e:
                s="readMQTT on_message %s: problem:  %s" % (broker, str(e))
                logging.exception(s)
                print (s)

        def on_disconnect(client, userdata, rc):
            #stopping subscriptionthread:
            mq = globals.mqttClients[broker]
            mq["toSubscribeQueue"].put("brokerDisconnectedEvent")    
            print("MQTT disconnected: " + client._client_id)

        def on_subscribe(client, userdata, mid, granted_qos):
            #import web_pdb; web_pdb.set_trace() #debugging
            #print ("MQTT subscribed callback qos is %d " % (granted_qos))
            pass

        client = mqttClient.Client(clientName)
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        client.on_subscribe = on_subscribe

        client.connect(broker, port, 60)
        client.loop_start()  # nonblocking; starts a thread.
        #client.loop_forever() 
            
    except Exception as e:
        logging.exception("MQTTServer: starting client connection %d; error %s" % (port, str(e)))
        try: 
            client.disconnect()  #try to clean up.
        except:
            pass #ignore
            
        client = None
        
    #if client is not None:
    #    print ("started MQTT client %s" % client._client_id)

    return client
#----------------------------------------------------------------------------------------------------
# set up memory for the broker connection  if not yet existing
def evInitializeBroker(broker):

    print("evInitializeBroker for %s " % broker)
    
    if broker not in globals.mqttClients: #start client:
        port = MQTTPORT
        clientName = "pvOpt_" + globals.hostName + "_" + broker
        #print("stating client for " + clientName)
        
        globals.mqttClients[broker] = {"client": start_MQTTclient(port, broker, clientName),
                                        "toSubscribeQueue" : queue.Queue(),
                                        "subscriptions" : set(), #set of confirmed subscriptions
                                        "subscriptionThread": None,  #thread handle
                                        "validUntil" : 0}
                                        #"values" : {} } 
    return globals.mqttClients[broker]

#----------------------------------------------------------------------------------------------------
# read_MQTT called via cache
# subscribes a topic, (if not already subscribed)
# cache and event is updated in callback onMessage()
#----------------------------------------------------------------------------------------------------
#
@logged(logging.DEBUG)
def read_MQTT(dp):
    
    rv = metadata.read("MQTT/" + dp, "MQTT/" + dp)    
    
    topic, broker = dp.split("@")
            
    if len(topic) == 0:  
        topic= "#"

    try:
        #set up client connection to the broker:
        mq=evInitializeBroker(broker)
        
        if mq["client"] is None:
            raise Exception('no MQTT client for %s' % (broker))
            
        if topic not in mq["subscriptions"]:
            mq["toSubscribeQueue"].put(topic)
            rv[5]="subscription enqueued"
            print ("enqueue %s" % topic)
        
        fullDp = "MQTT/" + dp
        cachedItem=globals.cache.getValue(fullDp)  #cache wird im on_message geschrieben...        
        if cachedItem is not None:
            #just update state:
            #rv[0], rv[1], rv[2], rv[3], rv[4] =cachedItem[0:5] #rv[5] is state (could be updated)
            rv = cachedItem
        else: #just update if not yet existin in cache.
            globals.cache.enterValue(fullDp, rv,10)        
            
        #return old cached value:
        #if topic in mq["values"]:
        #    rv[1], rv[3], rv[5] = mq["values"][topic] #only relevant data other come from metadata or is clear anyway.
            
    except Exception as e:
        logging.exception ( "MQTT: problem with %s" % (dp))
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "MQTT/%s" %(dp), "Exception"
                    
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
        try:
            mqttConfig = globals.config.configMap["MQTT"]    
            if "broker" in mqttConfig:
                broker=mqttConfig["broker"]
        except:
            pass
        l.append(broker)
        
    topic, broker = l[0:2]
    
    dp = topic +  "@" + broker        

    rv = globals.cache.get(dp, read_MQTT, 0)  #hier über den cache zu gehen ist vermutlich etwas überspitzt;

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
        try:
            mqttConfig = globals.config.configMap["MQTT"]    
            if "broker" in mqttConfig:
                broker=mqttConfig["broker"]
        except:
            pass
        l.append(broker)
        
    topic, broker = l[0:2]
    dp = topic +  "@" + broker        

    rv = metadata.read("MQTT/" + dp, "MQTT/" + dp)    
    rv [1] = value
    rv [5] = "Ok"
    
    if pulsetime is None:
        pulsetime = 0
  
    try:
        mq=evInitializeBroker(broker)
        print("MQTT raw_write publish %s=%s" % (topic,value))

        MQTTMessageInfo = mq["client"].publish(topic, payload=value, qos=0, retain=False)        
        if MQTTMessageInfo.rc != 0:
            s="MQTT publish to %s with Status %d (%s)" % (broker, rc, MQTTReturnCode[rc])
            print (s)
            raise Exception(s)
                        
    except Exception as e:
        logging.exception ( "MQTT:  problem with %s" % (dp))
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "MQTT/%s" %(dp), "Exception"

    print("MQTT raw_write returns %s" % str(rv))
    
    return rv    


#----------------------------------------------------------------------------------------------------
# write:
#   publishes a mqtt value
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
                i=i+1
                dp = "/".join(dpList[i:])
                state = read(dp)
                #print ("XOR: state " + str(state))                
                if (len(state)>1)  and state[5]=="Ok":
                    value = state[1] ^ value
                else:
                    s="cannot read, therefore cannot write XOR"
                    raise Exception(s)
                    
            globals.cache.invalidate(dp)
            rv = raw_write(dp, value, pulsetime)

    except Exception as e:
        logging.exception ( "writeMQTT problem with %s" % (dp))
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "MQTT/%s" %(dp), "Exception"

    return rv

#----------------------------------------------------------------------------------------------------
def cli():
    """Start via command line interface."""
    parser = argparse.ArgumentParser(
        description="tests MQTT brokers subscribes to given topic, publish test topic"
                    "  topic/subtopic/../../..@broker, wildcards are # and +")
    broker="loalhost"
    try:
        mqttConfig = globals.config.configMap["MQTT"]    
        if "broker" in mqttConfig:
            broker=mqttConfig["broker"]
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
                        help= "broker, mqtt server")

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
    
    workerThread = threading.Thread(target=worker, args = (None, ), name="MQTTserver_Worker")
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

    main()

