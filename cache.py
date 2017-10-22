#!/usr/bin/python3
import os, glob, time, sys, datetime, time

#import cache
import config
import driverCommon
import globals

import logging
from funcLog import logged
import threading



class CachedItem(object):
    def __init__(self, key, value, duration=1):
        self.key = key
        self.value = value
        self.duration = duration
        self.timeStamp = time.time()

    def __repr__(self):
        return '<CachedItem {%s:%s} expires at: %s>' % (self.key, self.value, self.timeStamp + self.duration)

class CachedDict(dict):

#--------------------------------------------
    def __init__(self):    

        self.autoRefreshduration = dict()
        self.autoRefreshfn = dict()
        self.t = threading.Thread(target=self.refreshThread, args = ( ))
        self.t.daemon = True
        self.t.start()


#--------------------------------------------
    @logged(logging.DEBUG)
    def getStamp (self, key):
        return self[key].timeStamp

#--------------------------------------------
# enter key into list for autoRefresh
    @logged(logging.DEBUG)
    def registerRefresh (self, key, fn, duration=1):
        self.autoRefreshduration[key]=duration
        self.autoRefreshfn[key]=fn        
        return 0

#--------------------------------------------
# refresh
    @logged(logging.DEBUG)
    def refreshThread (self):
        while 1:
            keys=self.autoRefreshfn.keys()  # darf nicht direkt verwendet werden, threading problematik
            for key in keys:
                try:
                    duration = self.autoRefreshduration[key]
                    #self[key].duration=0  # invalidate
                    r = self.get(key, self.autoRefreshfn[key], duration)
                    
                except  Exception as e:
                    logging.exception("cache.refreshThread")                
                    print ("RefreshThread: Exception %s" % (type(e).__name__))
                    print (str(e))
                    pass
                    
            time.sleep(2)
            
        return 0
        
#--------------------------------------------        
    @logged(logging.DEBUG)
    def invalidate(self, key):
        if key in self:
            self[key].timeStamp = 0
        
#--------------------------------------------        
    @logged(logging.DEBUG)
    def get(self, key, fn, duration=1):
        #if not hasattr(self,"m_history"):
        #    self.m_history={}  #leeres dict
        if key not in self \
        or self[key].timeStamp + duration < time.time():
            o = fn(key)
            self[key] = CachedItem(key, o, duration)
            # und jetzt in archive schreiben:
            #cache wird auch noch für "nichstandarddinge" wie ETH read_raw verwendet.
            # archive darf nur mit einem sinnvollen Tupel aufgerufen werden und auch nur wenn das read Ok war.
            if list == type(o) or tuple == type(o):
                status = "NOK"
                if len(o) > 4:            #ignore everything else!
                    status="Ok"
                    if len(o) > 5:
                        status=o[5]            
                if status == "Ok":            
                    globals.gArchive.write(o)
            
            #zusätzlich in history eintragen:
            #if key not in self.m_history:
            #    self.m_history[key]=[o]  #liste mit o anlegen für key
            #else:
            #    self.m_history[key].append(o)
            #logging.log(90, "cache: %s: %d items" % (key, len(self.m_history[key])))

        #else:
        #    print ("CACHE HIT for %s " % key)
        

        return self[key].value



if __name__ == '__main__':
    import config
    import driverCommon
    import globals
    with config.configClass() as configuration:
#    gConfig=configuration
        globals.config= configuration
        import readtemp
        cd = CachedDict()
        while 1:
            dps = ("TEMP/00042b8679ff", "TEMP/00042cb4d4ff", "TEMP/00042d9aabff")
            dats=[cd.get(dp, driverCommon.read) for dp in dps]
            for dat in dats:
                print (" %s %s %2.2f %s " % (dat[3].strftime("%H:%M:%S"), dat[0], dat[1], dat[2]),  end=" ")
            time.sleep(0.2)
            print ("")
            

