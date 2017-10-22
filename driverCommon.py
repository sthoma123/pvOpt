#!/usr/bin/python3
# from imp import reload
# driver.py
# implements read, write and getList function for all protocols:
#Action="read"/ "get"
#bei read:
#- Value ="0,1,..n"

#bei read: (fuer verdichten)
#- lastvalue = "0,1,..n" 
# - timeout (?)
#bei get fuer Archiveserver:
#- timeframe = {start / end} (unixtime?)
#Zu den Values: unit
#DP=prot/box/ID/SUBID/SUBSUBID
#prot=PV, ETH, TEMP


import os, time, sys, datetime
import readETH008 as ETH
import readPV as PV
import readHealth as HEALTH
import readtemp as TEMP
import readAlias as ALIAS
import readComp as COMP
import readDlms as DLMS
import readMOD as MOD
import readVar as VAR
try:
    import readHM as HM
except:
    pass
    
import config
import logging
from funcLog import logged
import globals
import cache
import urllib.request
import urllib.error
import json
import JSONHelper
import archive

import eventhandler


#----------------------------------------------------------
#
# writes 1 data uncached
#
#
@logged(logging.DEBUG)
def write1(dp, data, pulse):
    rv = None
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    while len(dpList) < 2:  # brauche zuminest 2 elemente, auch wenn sie leer sind!
        dpList += [""]
        
    if dpList[0] == "": # kein protokoll!!!
       dpList[0] = "PV"  # default!
       
    pu=""
    if not pulse is None:
        pu = ", pulse"
       
    cmd= dpList[0] + ".write('"  + "/".join(dpList[1:]) + "', data" + pu +" )"
    
    #logging.error("about to execute " + cmd)
    
    try:
        rv=eval(cmd)
    except Exception as e:
        rv = "driverCommon write1 Exception %s for %s, data is %s" % (type(e).__name__, cmd, str(data)), 0, "~" , datetime.datetime.now(), dp, "Exception"
        logging.exception("driverCommon.py")
    
    return rv



#----------------------------------------------------------
#
# read1
#
#
@logged(logging.DEBUG)
def read1(dp):
    rv = None
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    while len(dpList) < 2:  # brauche zuminest 2 elemente, auch wenn sie leer sind!
        dpList += [""]
        
    if dpList[0] == "": # kein protokoll!!!
       dpList[0] = "PV"  # default!
       
    cmd= dpList[0] + ".read('"  + "/".join(dpList[1:]) + "')"
    
    #logging.Error("about to execute " + cmd)
    
    try:
        rv=eval(cmd)
        
        if rv[5]== "Ok":
            eventhandler.enqueue(eventhandler.READEvent, rv[3], rv[4], rv[3])
        
    except Exception as e:
        rv = "driverCommon read1 Exception %s for %s" % (type(e).__name__, cmd), 0, "~" , datetime.datetime.now(), dp, "Exception"
        logging.exception("driverCommon.py")
    
    return rv

#--------------------------------
# reads datapoint from string
# returns tuple
#
@logged(logging.DEBUG)
def read(dp, maxAge = 10):
    
    #print ("drivercommon.read called with " + dp)
    
    if globals.cache is None:
        globals.cache = cache.CachedDict()

    if globals.config is None:
        with config.configClass() as configuration:
#    gConfig=configuration
            globals.config= configuration
            rv=globals.cache.get(dp, read1, maxAge)
            globals.config = None
    else:
        rv=globals.cache.get(dp, read1, maxAge)
    
    return rv

#--------------------------------
# writes 1 datapoint 
# returns status
#
@logged(logging.DEBUG)
def write(dp, data, pulse=None):
    
    if globals.cache is None:
        globals.cache = cache.CachedDict()

    if globals.config is None:
        with config.configClass() as configuration:
#    gConfig=configuration
            globals.config= configuration
            rv=write1(dp,data, pulse)
            globals.config = None
    else:
        rv=write1(dp,data, pulse)    

    return rv
    
#--------------------------------
# gets list of strings, 
# returns list of tuples
#
@logged(logging.DEBUG)
def readMulti(dps, maxAge = 10):

    #print ("readMulti kriegt %s" % str(dps) + str(type(dps)))

    if dps is None or dps == "":
        dps = ("PV/PV0", "PV/PV1", "TEMP/00042b8679ff", "TEMP/00042cb4d4ff", "TEMP/00042d9aabff", "ETH/kellerschalter/3","ETH/kellerschalter")
        
    if type(dps) is str: # mach eine liste draus
        dps=[dps,]
    
    dats=[read(dp, maxAge) for dp in dps]        

    return (dats)

#--------------------------------
# read1Archive

@logged(logging.DEBUG)
def read1Archive(dp, timeStamp, n, timeDelta, operation, timeStampTo):

    #print ("read1Archive ", dp, n, timeStamp)
    data=globals.gArchive.read(dp, timeStamp, n, timeDelta, operation, timeStampTo) 
    
    return data

#--------------------------------
# get1InfoArchive

@logged(logging.DEBUG)
def getInfo1Archive(dp):

    data=globals.gArchive.getInfo(dp)     
    return data

#--------------------------------
# getInfoArchive
#--------------------------------
@logged(logging.DEBUG)
def getInfoArchive(dp):

    if globals.config is None:
        with config.configClass() as configuration:
#    gConfig=configuration
            globals.config= configuration
            rv=getInfo1Archive(dp)
            globals.config = None
    else:
        rv=getInfo1Archive(dp)
    
    #print("drivercommon.getInfoArchive returnes ", rv)
    
    return rv

#--------------------------------
@logged(logging.DEBUG)
def getDatapointsArchive():

    if globals.config is None:
        with config.configClass() as configuration:
#    gConfig=configuration
            globals.config= configuration
            rv=globals.gArchive.getDatapoints()
            globals.config = None
    else:
        rv=globals.gArchive.getDatapoints()
    
    return rv

#--------------------------------
# readArchiveMulti
#    dp is a list of datapoints 
#    um einigermassen kompatibel zu meiner read-struktur zu bleiben ist der output:
#       [0] description
#       [1] list of values / timestamp pairs
#       [2] unit
#       [3] timestamp (now)
#       [4] original datapoint name
#       [5] "Ok" (if anything found)
#       [6] ""
#--------------------------------
@logged(logging.DEBUG)
def readArchiveMulti(dps, timeStamp, n, timeDelta = None, operation = None, timeStampTo = None):

    if type(dps) is str: # mach eine liste draus
        dps=[dps,]
        
    rv = list()
    
    print ("readArchiveMulti " + str(dps))
    
    for dp in dps:
        rv1 = [""] * 7  # empty list with 0..6
        info = getInfoArchive(dp)
        if isinstance(info, (list, tuple)):
            rv1[0]=info[0] # desc
            rv1[2]=info[1] # unit
            rv1[3]=info[2] # timestamp
            rv1[4]=info[6] # dp 
            rv1[5]="Ok"
            
        rv1[1] = readArchive(dp, timeStamp, n, timeDelta, operation, timeStampTo)
        
        print ("readArchiveMulti dp " + str(dp) + " --- " + str(rv1))
        
        rv.append(rv1)

    print ("readArchiveMulti returns " + str(rv))
    
    return (rv)

    
#--------------------------------
# readArchive
#--------------------------------
@logged(logging.DEBUG)
def readArchive(dp, timeStamp, n, timeDelta = None, operation = None, timeStampTo = None):
    #print ("drivercommon.readArchive called with " , dp, timeStamp, n)
    
    if globals.config is None:
        with config.configClass() as configuration:
#    gConfig=configuration
            globals.config= configuration
            rv=read1Archive(dp, timeStamp, n, timeDelta, operation, timeStampTo)
            globals.config = None
    else:
        rv=read1Archive(dp, timeStamp, n, timeDelta, operation, timeStampTo)
    
    #print("drivercommon.readArchive returnes ", rv)
    
    return rv

#--------------------------------
# from imp import reload
# writes one dp given as string via web
# returns string result (OK or not).
#
@logged(logging.DEBUG)
def writeViaWeb(dp, data, target="", pulse = None):
    #with config.configClass() as configuration:

    if target == "":
        target = globals.config.defaultServer           
           
    jData = JSONHelper.encodeParm(data)
            
    url='http://{target}/write?dp={dp}&data={data}'.format(target=target, 
        dp=JSONHelper.encodeParm(dp), 
        data=jData)

    if not pulse is None:
        jPulse = JSONHelper.encodeParm(pulse)
        url=url + '&pulse={pulse}'.format(pulse=jPulse) 
    
    #print ("writeViaWeb: url is %s" % url)
    try:
        #print ("server returned" + url)
        f =  urllib.request.urlopen(url)
        s = f.read()
        s= s.decode(encoding='UTF-8')
        #print ("server returned" + s)
        rv = JSONHelper.decodeParm(s)

        
    except  Exception as e:
        rv  ="writeViaWeb cannot open url %s" % url
        rv += str(e)
        rv =[rv]
        #print (rv) 

    return (rv)

    
#--------------------------------
# from imp import reload
# reads one dp given as string via web
# returns result as list.
#
@logged(logging.DEBUG)
def readViaWeb(dp, maxAge = None, target = ""):    
    
    if target == "":
        target = globals.config.defaultServer
           
    #if "?" in dp:  #servername given
    #    x=dp.split("?",1)
    #    #print (x)
    #    target=x[0]
    #    dp=x[1]
            
    url='http://{target}/read?dp={dp}'.format(target=target, dp=JSONHelper.encodeParm(dp))
    
    
    #print ("url is %s" % url)
    try:
        f =  urllib.request.urlopen(url)
        s = f.read()
        s= s.decode(encoding='UTF-8')
        #print ("server returned" + s)
        rv = JSONHelper.decodeParm(s)

        
    except  Exception as e:
        rv  ="readViaWeb cannot open url %s" % url
        rv += str(e)
        rv =[rv]
        #print (rv) 

    return (rv)

#--------------------------------
# reads several dps given as jsonified string via web
# returns list of lists
#
@logged(logging.DEBUG)
def readMultiViaWeb(dps, maxAge = None, target = ""):    
    
    if target == "":
        target = globals.config.defaultServer
       
    
    url="http://{target}/readMulti?dp={dps}".format(target=target, dps=JSONHelper.encodeParm(dps))

    
    #print ("url is %s" % url)
    #f =  urllib.request.urlopen(url)
    #s = f.read()
    #s= s.decode(encoding='UTF-8')
    
    try:
        #print("readMultiViaWeb: 1 " + url)
        f =  urllib.request.urlopen(url, timeout=20)  #fuer timeout 10 ist manchmal zu langsam.
        logging.debug("readMultiViaWeb requests: %s" % (url))
        s = f.read()
        #print("yyy readMultiViaWeb: 2 " ,  s)
        s= s.decode(encoding='UTF-8')
        #logging.debug("readMultiViaWeb server returned after decode: %s" % (s))
        #print ("server returned" + s)
        if len(s) > 0 :
            rv = JSONHelper.decodeParm(s)  #returned list of tupes (4th parm is date)
            #logging.error("xxxreadMultiViaWeb JSONdecode : %s" % (rv))
            #logging.debug("readMultiViaWeb after decodeparm: %s" % (rv))
            #print("readMultiViaWeb: 3 " ,  rv)
            #for i in range(len(rv)):
            #    if len(rv[i])>3:
            #        rv[i][3]=datetime.datetime.strptime(rv[i][3], '%Y-%m-%dT%H:%M:%S.%f')
            
        else:
            rv = ""

    except  Exception as e:
        rv  = "readMultiViaWeb cannot open url %s, %s" % (url, type(e).__name__)
        rv += str(e)
        rv = ["ERROR", rv]
        logging.exception("driverCommon.py")
        #print (rv) 
        
    return (rv)

#----------------------------------------------------------
    
#----------------------------------------------------------
#
# readArchiveViaWeb
#
#
@logged(logging.DEBUG)
def readArchiveViaWeb(dp, timeStamp, n, target = "", timeStampTo = None):
    #with config.configClass() as configuration:

        if target == "":
            target = globals.gConfig.defaultServer[0]

        url='http://{target}/readArchive?dp={dp}&n={n}&timeStamp={timeStamp}'.format(target=target, dp=JSONHelper.encodeParm(dp), n=JSONHelper.encodeParm(n), timeStamp=JSONHelper.encodeParm(timeStamp))
        if not timeStampTo is None:
           url = url + "& timeStampTo={timeStamp}" % JSONHelper.encodeParm(timeStampTo)
        
        #logging.error("readArchive url %s" % url)
        
        #print ("url is %s" % url)
        try:
            f =  urllib.request.urlopen(url)
            s = f.read()
            s= s.decode(encoding='UTF-8')
            #print ("readArchiveViaWeb: server returned" + s)
            rv = JSONHelper.decodeParm(s)

            
        except  Exception as e:
            rv  ="readArchiveViaWeb cannot open url %s" % url
            rv += str(e)
            rv =[rv]
            #print (rv) 

        return (rv)

#----------------------------------------------------------
#
# getInfoArchiveViaWeb
#
#
@logged(logging.DEBUG)
def getInfoArchiveViaWeb(dp, target = ""):
    #with config.configClass() as configuration:

        if target == "":
            target = globals.gConfig.defaultServer[0]

        url='http://{target}/getInfoArchive?dp={dp}'.format(target=target, dp=JSONHelper.encodeParm(dp))
        
        #print ("url is %s" % url)
        try:
            f =  urllib.request.urlopen(url)
            s = f.read()
            s= s.decode(encoding='UTF-8')
            #print ("readArchiveViaWeb: server returned" + s)
            rv = JSONHelper.decodeParm(s)

            
        except  Exception as e:
            rv  ="readArchiveViaWeb cannot open url %s" % url
            rv += str(e)
            rv =[rv]
            #print (rv) 

        return (rv)

        
    
#---------------------------------------------------------------------------------------
if __name__ == "__main__":
    with config.configClass() as configuration:
        globals.config= configuration
        print ("try: driverCommon.py -l debug")
        logging.getLogger().setLevel(logging.DEBUG)
        
        if True:
            dps = ("VAR/AUTOBOILER",)
            target= "kr:8000"
            print ("readMultiViaWeb (%s, %s)" % (dps, target))
            dats = readMultiViaWeb(dps, target=target)        
            print ("returns " + str(dats))

        if False:
            dps = ("MOD/ttyUSB.modbus/1/ZAEHLER/P1Power", "MOD/ttyUSB.modbus/2/ZAEHLER/P1Power")
            target= "zr:8000"
            print ("readMultiViaWeb (%s, %s)" % (dps, target))
            dats = readMultiViaWeb(dps, target=target)        
            print ("returns " + str(dats))

        if False:
            dp="ETH/Wohnzimmer/V"
            x=read(dp)
            print ("normal: ", x, type(x[1]))
            x=readViaWeb(dp, "kellerRaspi:8000")
            print ("viaWeb: ", x, type(x[1]))
            x=readMultiViaWeb(("ETH/Kellerschalter/8", "ETH/Wohnzimmer/V") , target="kellerRaspi:8000")
            print ("MultiviaWeb: ", x, type(x[0][1]))
            
        if False:
            dp="ETH/Wohnzimmer/9"
            dps= ("ETH/Kellerschalter/8", "ETH/Wohnzimmer/V", "ETH/Kueche/V")
            x=readMultiViaWeb(dps , target="zaehlerraspi:8000")
            print ("multiviaweb ", x, type(x[0][1]))
            while 0:
                writeViaWeb(dp, True, "kellerRaspi:8000")
                writeViaWeb(dp, False, "kellerRaspi:8000")

        if False:
            dp="comp_pvtotal_p[0]_p[1]__pv_pv0__ _pv_pv1_"
            #print ("getInfo ",  getInfoArchive(dp))
            print ("getInfoViaWeb: ", getInfoArchiveViaWeb(dp, "localhost:8000"))
            
        if False:
            dp="VAR/ZAEHLERBILANZ"
            target= "kellerRaspi:8000"
            while 1:
                writeViaWeb(dp, 123, target)
                writeViaWeb(dp, 345, target)
                
                
        #dpwrite= "aaphr0?VAR/nonsensedatapoint"
        #s = writeViaWeb(dpwrite, 987)
        #print ("Write returned %s " % (s))
        
        #s = read(dpwrite)
        #print ("read returned %s " % (str(s)))
        
        
        

        
