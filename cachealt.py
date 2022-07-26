#!/usr/bin/python3
import os, glob, time, gspread, sys, datetime

import time

class CachedItem(object):
    def __init__(self, key, value, duration=5):
        self.key = key
        self.value = value
        self.duration = duration
        self.timeStamp = time.time()

    def __repr__(self):
        return '<CachedItem {%s:%s} expires at: %s>' % (self.key, self.value, self.timeStamp + self.duration)

class CachedDict(dict):

    def getStamp (self, key):
        return self[key].timeStamp
        
    def get(self, key, fn, duration=10):
        if key not in self \
            or self[key].timeStamp + self[key].duration < time.time():
                o = fn(key)
                self[key] = CachedItem(key, o, duration)
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
            

