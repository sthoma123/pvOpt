#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß

#
#  returned copied item instead of cached item because ALIAS modifies list (datapoint)
#
print ("imported " + __name__)

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
    
        #refresh wird nur von read_dlms_raw verwendet, da der Wert _immer_ aus dem cache zurückgeliefert wird, da das read_raw extrem lange dauert.
        # die Frage ist, ob das nicht besser über einen Timer und einer cache-invalidation gemacht wird...
        #
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
                    
            time.sleep(10)
            
        return 0


#--------------------------------------------        
# e.g. for spontaneous values like in MQTT.
#
#
    def enterValue(self, key, rv, duration):
        self[key] = CachedItem(key, rv, duration)
        if list == type(rv) or tuple == type(rv):
            status = "NOK"
            if len(rv) > 4:            #ignore everything else!
                status="Ok"
                if len(rv) > 5:
                    status=rv[5]            
            if status == "Ok":            
                globals.gArchive.write(rv)

    def getValue(self, key):
        rv = None
        if key in self:
            rv = self[key].value
            
        xrv = rv
        try:
            xrv = rv.copy()
        except:
            pass
        return xrv

#--------------------------------------------        
    @logged(logging.DEBUG)
    def invalidate(self, key):
        if key in self:
            self[key].timeStamp = 0
        
#--------------------------------------------        
    @logged(logging.DEBUG)
    def get(self, key, fn, duration=1):     #duration is maxAge
        #if not hasattr(self,"m_history"):
        #    self.m_history={}  #leeres dict
        rv = None
        
        if key not in self \
        or self[key].timeStamp + duration < time.time():
            if duration > 999998:  # do not read, issue a warning (needed for fast compile that does not rely on real data)
                rv = "Warning: no cached data for %s" % (key), 0, "~" , datetime.datetime.now(), key, "Warning"
            else:
                #cache miss; try to read from driver
                rv = fn(key)   
                #print ("cache  function returned %s for %s" % (rv[5], rv[1]))
                
                #if len(rv) > 5:
                #    #print ("cache got %s " % rv[5])
                #    if rv[5]=="subscription enqueued": # a rather temporary return: reduce duration of validity
                #        duration = -1
                #        #print ("cache duration reduced")

                #if duration>=0: #do not cache if not Ok...
                self[key] = CachedItem(key, rv, duration)
                    
                # und jetzt in archive schreiben:
                #cache wird auch noch für "nichstandarddinge" wie ETH read_raw verwendet.
                # archive darf nur mit einem sinnvollen Tupel aufgerufen werden und auch nur wenn das read Ok war.
                if list == type(rv) or tuple == type(rv):
                    status = "NOK"
                    if len(rv) > 4:            #ignore everything else!
                        status="Ok"
                        if len(rv) > 5:
                            status=rv[5]            
                    if status == "Ok":            
                        globals.gArchive.write(rv)
                
        else:
            rv = self[key].value 
            #while len(rv)<=6: #just a hint for the reader:
            #    rv.append("")
            #rv[6]="cached"

        #since the caller might modify the returned buffer, I have to clone it:
        
        xrv = rv
        try:
            xrv = rv.copy()
        except:
            pass
        return xrv



if __name__ == '__main__':
    import config
    import driverCommon
    import globals
    with config.configClass() as configuration:
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
            

