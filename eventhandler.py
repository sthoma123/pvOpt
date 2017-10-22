#!/usr/bin/python3

#der eventhandler verwaltet/verteilt alle events (read-events etc.)
#bekommt alle events von drivercommon und listeners ueber eine (1) queue
#
# basis fuer die MQTT kommunikation
# aufteilung, vereinfachung von events (leistungsspruenge konfigurierbar in lesbare events)
#
#
#
import os, glob, time,  sys, datetime
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

READEvent = 1
WRITEEvent = 2
EXTEvent = 3  #like button pressed from eth boards, usually via ip request
TIMEREvent = 4  #periodische oder einmalige

class event():
    def __init__(self, type, source, value, srcTime=None):
        self.type = type
        self.source = source
        self.value = value     
        if srcTime is None:
            srcTime = datetime.datetime.now()
        self.srcTime = srcTime
        
        print("event constructor: %s" % (str(source)))
        
#----------------------------------------------------------------------------------------------------
#//wird von den workers aufgerufen
#stellt alles prinzipiell nur in die queue.
# source ist ein gueltiger datenpunkt
# type ist ein typeOfEventEnum
# value ist direkt der Wert (nicht die Liste aus den read-funktionen)
# srcTime: wenn von der eventquelle geliefert wird, sonst wird now draus gemacht.
#
def enqueue(type, source, value, srcTime=None):
#mache eventclass aus dem event

    globals.eventQueue.put(event(type, source, value, srcTime))
    return 0
   
#----------------------------------------------------------------------------------------------------
#  
#
def transform(item, context):
    return item
    
#----------------------------------------------------------------------------------------------------
#  
#
def flow(item, context):
    #check for abonments, individual flows, then forward it to the node-red flowhandler
    return item;

#----------------------------------------------------------------------------------------------------
# worker:
# wird als thread gestartet,
# liest aus der Queue
#
def worker(dummy):

    globals.eventQueue = queue.Queue()
    
    context={} #vielleicht mach ich den einmal persistent! da kann sich jedes Event (Source) die Vergangenheit merken.

    while (not globals.shutdown):
        item = globals.eventQueue.get()
        print ("got item %s" % str(item))
        item = transform(item, context) # dort wird z.b. ein energie Leistungssprung auf ein spezifisches Geraet transformiert (mit context damit ich ein bisschen mitteln kann, bei mehreren messwerten)
        if item is not None:
            item = flow(item, context)
        globals.eventQueue.task_done()
        
                