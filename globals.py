#!/usr/bin/python3
# globals for logging und configuration 

import cache as ca
import config
import configparser
import archive
import socket
import threading

# fill gConfig
try:
    print(type(gConfig))
except:
    gConfig = config.configClass()

# fill cache
try:
    print(type(cache))
except:
    cache =  ca.CachedDict()

# fill ethcache
try:
    print(type(ethcache))
except:
    ethcache =  ca.CachedDict()

# fill archiveCache
try:
    print(type(archiveCache))
except:
    archiveCache =  ca.CachedDict()
    print ("ARCHIVECACHE established")

# fill obisConfig
try:
    print(type(OBISconfig))
except:
  OBISconfig = configparser.ConfigParser()
  OBISconfig.read('/etc/obis.ini')

# fill archive
try:
    print(type(gArchive))
except:
    gArchive = archive.archiveClass()
    

# fill MODport
try:
    print(type(MODport))
except:
    MODport =  dict()
    #l["ID"]=[id]

# fill var (variables)
try:
    print(type(var))
except:
    var =  dict()
    var["test"]=21
    #l["ID"]=[id]

hostName = socket.gethostname()
modbusSema = threading.Semaphore() # just 1 thread may use modbus!
shutdown = False  # used for server to exit (and restart?)
restart  = False
modbusQuality  = 100 # restart when zero (decrement by 10 for each read error, increment by 1 for each success)
listOfOpenFiles = []
#eventQueue = False


