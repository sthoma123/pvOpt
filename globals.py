#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
# globals for logging und configuration 

print ("imported " + __name__)

import cache as ca
import config
import configparser
import archive
import socket
import threading

# create empty sessionContext
try:
    dummy=type(gSessionContext)
except:
    gSessionContext = dict()

    
# fill config
try:
    dummy=type(config)
except:
    config = config.configClass()

# fill cache
try:
    dummy=type(cache)
except:
    cache =  ca.CachedDict()

# fill ethcache
try:
    dummy=type(ethcache)
except:
    ethcache =  ca.CachedDict()
        
# fill archiveCache
try:
    dummy=type(archiveCache)
except:
    archiveCache =  ca.CachedDict()

# fill obisConfig
try:
    dummy=type(OBISconfig)
except:
  OBISconfig = configparser.ConfigParser()
  OBISconfig.read('/etc/obis.ini')

# fill archive
try:
    dummy=type(gArchive)
except:
    gArchive = archive.archiveClass()
    

# fill MODport
try:
    dummy=type(MODport)
except:
    MODport =  dict()
    #l["ID"]=[id]

# fill var (variables)
try:
    dummy=type(var)
except:
    var =  dict()
    var["test"]=21
    #l["ID"]=[id]

# non-persistent logging per datapoint
# used by dpLogger
try:
    dummy=type(dpLog)
except:
    dpLog = dict()


hostName = socket.gethostname()
modbusSema = threading.Semaphore() # just 1 thread may use modbus!
shutdown = False  # used for server to exit (and restart?)
restart  = False
modbusQuality  = {} # number of unsuccessfull reads from a device per device
listOfOpenFiles = []
listOfOpenFilesLock = threading.Lock()  # to protect listOfOpenFiles
#eventQueue = False


