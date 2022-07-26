#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
#"""
# from https://larsmichelsen.github.io/pmatic/doc/index.html
#
#  readHM Homematic interface (uses pmatic (and xmlapi?))
#  dp is ("HM/address/property") 
#  HM/address/channel/property
# e.g. HM_CC_RT_DN123/4/ACTUAL_TEMPERATURE
# uses pushover.net for notifications
# start specific hm scripts (pmatic manager)
#writ:
#value (float)
#press (short long) (device.button(0).press_short()

#property "summary_state" -> printable device state as string
#sonnenstand pmatic.utils.sun_position  (-> daraus max soll-leistung)
#
#
#import pmatic
#ccu = pmatic.CCU (address="hmraspi", credentials=("Admin", ""))
#d=ccu.devices.get("NEQ1489656")
#c=d.channels
#k=c[4].values.keys()
#v=c[4].values["ACTUAL_TEMPERATURE"].value
#
#
#address is serial number
# a list of all datapoints can be read by invoking the main function of this module.
#
#
# address wie in pmatic definiert
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
#import http, http.client
import argparse
import json
import config
if __name__ == '__main__':
    config.doNotParseCommandline = True


import globals
from funcLog import logged
import logging

import pmatic
import metadata
import helpers


#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read_HM_property(ccu, property): 
    try:
        rv = ""
        pass    
    except:
        #print ('unable to retrieve data from ' + wechselrichter)
        #print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
        return None
    return rv



#----------------------------------------------------------------------------------------------------
#
@logged(logging.DEBUG)
def read_hm(dp):
    rv = metadata.read("HM/" + dp, "HM/" + dp)    
    
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    while len(dpList) < 2:  # brauche zuminest 2 elemente, auch wenn sie leer sind!
        dpList += [""]
        
    ## do not issue too many requests if there is a session problem:
    try:
        HMDeferred = globals.HMDeferred
        #"mqttClient" in dir(globals)
    except:
        globals.HMDeferred = time.time() - 1
        
    retry = 3
    if globals.HMDeferred > time.time():
        rv = "HM down", 0, "~" , datetime.datetime.now() , "HM/%s" %(dp), "HM down"
        retry = 0

    #import web_pdb; web_pdb.set_trace() #debugging

    try:
        while retry > 0:
            retry -= 1
            try:
                ccu = globals.ccu
                if ccu is None:
                    raise
            except:
                ccuAddr = dpList[0]
                globals.ccu = pmatic.CCU (address=ccuAddr, credentials=("Admin", ""))            
                print ("readHM NEW CCU object for HM: %s" % (ccuAddr))
                ccu = globals.ccu
                
            try:
                address=""
                channel=-1
                key=""
                if len(dpList)>=2:                    
                    address=dpList[1]
                    if address != "":                        
                        dev = ccu.devices.get(address)  #return list of channels
                if len(dpList)>=3:
                    channel=int(dpList[2])
                    c = dev.channels[channel]
                if len(dpList)>=4:
                    key=dpList[3]
                    
                if address == "":   #only ccu given returns string of all datapoints incl stati
                    s=""
                    for x in ccu.devices.addresses():
                        s += "HM/%s/%s, " % (dpList[0], x)
                        print("(HM/%s/%s, %s %s)" % (dpList[0], x, ccu.devices.get(x).name, ccu.devices.get(x).summary_state))
                        
                    rv[1] = s
                    rv[5] = "Ok"
                elif channel== -1:  #no channel given, but device address
                    #returns properties of device
                    s=""
                    for i in range(len(dev.channels)):
                        x = dev.channels[i]
                        s += "HM/%s/%s/%s, " % (dpList[0], dev.address, str(i))
                        print ("(HM/%s/%s/%s, %s, %s, %s" % (dpList[0], dev.address, str(i), dev.name, x.name, x.summary_state))
                        
                    rv[0] = dev.name
                    rv[1] = s
                    rv[5] = "Ok"
                    
                elif key == "":  #channel given but no key (propery)
                    #returns keys of channel
                    s=""
                    k=c.values.keys() # values ist ein dict
                    print("%s of %s" % (c.name,dev.name))
                    for key in k:
                        try:
                            v=c.values[key].value
                        except Exception as e:
                            v="not a value"
                            #print("Exception %s, %s" % (type(e).__name__, e.args))
                            
                        s += "HM/%s/%s/%s/%s, " % (dpList[0], dev.address, str(channel), key)
                        print ("   (HM/%s/%s/%s/%s, %s)" % (dpList[0], dev.address, str(channel), key, str(v)))
                        
                    rv[0] = "%s of %s" % (c.name,dev.name)
                    rv[1] = s
                    rv[5] = "Ok"
                elif len(dpList) < 5:  #also key (property) given
                    s=""
                    k=c.values.keys() # values ist ein dict mit value und unit etc
                    print("%s of %s has %s" % (c.name,dev.name, k))
                    v=""
                    unit=""
                    try:
                        x=c.values[key]
                        v=x.value
                        unit=x.unit
                    except Exception as e:
                        v="%s of %s has no value" %(c.name,dev.name)
                    print ("   (HM/%s/%s/%s/%s, %s)" % (dpList[0], dev.address, str(channel), key, str(v)))
                        
                    rv[0] = "%s of %s" % (c.name,dev.name)
                    rv[1] = v
                    rv[2] = unit
                    rv[5] = "Ok"
                break

            except Exception as e:
                print("HM exception %s %s " % (type(e).__name__, e.args))
#readHM NEW CCU object for HM: HMRASPI
#HM exception KeyError ('device_id',)
                
                globals.ccu = None  #eventuell die Verbindung neu aufbauen.
                if retry == 0:                    
                    print ("setting HMDeferred")
                    globals.HMDeferred = time.time() + 360 #seconds; probably better configurable...
                    raise e
    except Exception as e:
        logging.exception ( "HM: problem with %s" % (dp))
        rv = "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "HM/%s" %(dp), "Exception"
                    
    return rv    
        
    


#----------------------------------------------------------------------------------------------------
# read takes defined datapoint syntax:
# takes list or string: /hmbox/ID/SUBID/SUBSUBID
# returns list: Name, Value, Unit, timestamp
def read(dp):

    rv = None

    rv = globals.cache.get(dp, read_hm, 10)

    return rv

#----------------------------------------------------------------------------------------------------
# raw_write
#
#
#
def raw_write (dp, value, pulsetime):

    rv = metadata.read("HM/" + dp, "HM/" + dp)    
    rv [1] = value
    globals.var[dp] = value
    rv [5] = "Ok"
    
    if pulsetime is None:
        pulsetime = 0
        
        
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    if len(dpList) < 4:  # brauche zuminest 4 elemente
        rv [5] = "Error, please supply at least 4 elements in dp"
    else:
        retry = 3
        if globals.HMDeferred > time.time():
            rv = "HM Deferred", 0, "~" , datetime.datetime.now() , "HM/%s" %(dp), "HM Deferred"
            retry = 0

        retry = 3
        try:
            while retry > 0:
                retry -= 1
                try:
                    ccu = globals.ccu
                    if ccu is None:
                        raise
                except:
                    ccuAddr = dpList[0]
                    globals.ccu = pmatic.CCU (address=ccuAddr, credentials=("Admin", ""))            
                    print ("readHM NEW CCU object ")
                    ccu = globals.ccu

                try:
                    address=""
                    channel=-1
                    key=""
                    unit = ""
                    if len(dpList)>=2:
                        address=dpList[1]
                        dev = ccu.devices.get(address)
                    if len(dpList)>=3:
                        channel=int(dpList[2])
                        c = dev.channels[channel]
                    if len(dpList)>=4:
                        key=dpList[3]
                        
                    if key == "":
                        key = "STATE" # more or less default for HM-Switches.
                        
                    s=""
                    k=c.values.keys() # values ist ein dict mit value und unit etc
                    print("%s of %s has %s" % (c.name,dev.name, k))
                    try:
                        print ("Pulsetime is %s " %(str(type(pulsetime))), pulsetime)
                        if type(pulsetime) is int or type(pulsetime) is float:
                            if pulsetime > 0:
                                if "ON_TIME" in k:  # ich kann meine pulsetime reinstellen!
                                    print ("ding kann ON_TIME")
                                    print("setze ON_TIME to %s" % str(pulsetime))
                                    p=c.values["ON_TIME"]
                                    p.value = pulsetime
                                else:
                                    s=("pulsetime given for %s but no property in HM %s %s" %(dp, dev.name, c.name))
                                    log.warning(s)
                                    print(s)
                                    
                        x=c.values[key]                        
                        print ("readHM try to set value to %s" %str(value))
                        
                        x.value = helpers.myConvert(value, type(x.value))  # wirft PMActionFailed exception wenn ncht writeable.
                        v=x.value # ruecklesen
                        unit=x.unit
                        rv[5] = "Ok"
                        print ("   (HM/%s/%s/%s/%s, %s)" % (dpList[0], dev.address, str(channel), key, str(v)))
                    except Exception as e:
                        v="%s of %s setting value exception" %(c.name,dev.name)
                        rv[5] = "Exception %s, %s" % (type(e).__name__, e.args)
                        logging.exception ( "HM: cannot set %s" % (dp))
                        retry = 0
                        break # vermutlich kein sessionproblem, das ein retry rechtfertigt.
                        
                    rv[0] = "%s of %s" % (c.name,dev.name)
                    rv[1] = v
                    rv[2] = unit

                    break  # kein retry

                except Exception as ex:
                    globals.ccu = None  #eventuell die Verbindung neu aufbauen.
                    if retry == 0:
                        print ("setting HMDeferred")
                        globals.HMDeferred = time.time() + 360 #seconds; probably better configurable...
                        raise ex
                        
        except Exception as e:
            logging.exception ( "HM: after retries problem with %s" % (dp))
            rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "HM/%s" %(dp), "Exception"
                    
    return rv    
        
                    
                    


#----------------------------------------------------------------------------------------------------
# write:
#   writes a HomeMatic value
#
@logged(logging.DEBUG)
def write(dp, value, pulsetime=None):  #3rd parameter needed for some other providers...
    # two methods for toggling: either with "XOR" in the datapoint or by "TOGGLE" as Value
    

    try:
        if type(dp) is str:
            dpList=dp.split('/')
        else:
            dpList=dp

        if value == "TOGGLE":
            state = read(dp)
            value = state[1] ^ 1
            
        if len(dpList) > 1:
            i=0
            if dpList[i]=="XOR":
                i=i+1
                dp = "/".join(dpList[i:])
                state = read(dp)
                #print ("XOR: state " + str(state))                
                if (len(state)>1) and state[5]=="Ok":
                    value = state[1] ^ value
                    
            globals.cache.invalidate(dp)
            rv =  raw_write(dp, value, pulsetime)

    except Exception as e:
        logging.exception ( "writeETH problem with %s" % (dp))
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "ETH/%s" %(dp), "Exception"


    return rv


#----------------------------------------------------------------------------------------------------
def cli():
    """Start the command line interface."""
    parser = argparse.ArgumentParser(
        description="reads homematic ccu, give homematic datapoint nn the form "
                    "  address/channel/property ")
    parser.add_argument("-d", "--dp", metavar='Datapoint',
                        type=str, default = "/",  #NEQ1489656/4/ACTUAL_TEMPERATURE
                        help="datapoint in the form address/channel/property")
                        
    parser.add_argument("-c", "--ccu", 
                        type=str, default = "HMRASPI",
                        help="CCU servername")

    parser.add_argument("-v", "--value", 
                        type=str, default = "",
                        help="value")

    parser.add_argument("-p", "--pulse", 
                        type=str, default = 0,
                        help="pulsetime in seconds")

    args = parser.parse_args()

    if all(arg in (False, None) for arg in (
            args.dp, args.ccu)):
        parser.print_help()
    
    return (args.ccu, args.dp, args.value, args.pulse)


    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main() :

  config.doNotParseCommandline = True  
  hmAddress, dp, value, pulse = cli()
  
  with config.configClass() as configuration:
    globals.config= configuration
    #hmAddress=globals.config.configMap["homeMatic"]


    while 1:
        print ("got %s, %s, %s, %s"%(hmAddress, dp, value, pulse))
        if dp[0] != "/":
            fullDP =hmAddress + "/" + dp 
        else:
            fullDP =hmAddress + dp 
            
        print ("")
        if value != "":
            print("write %s returns " % fullDP, write(fullDP, value, pulse))
        else:
            print("read %s returns " % fullDP, read(fullDP))
        print ("")
        break
    
    while 0:
        dp=hmAddress
        print ("")
        print("read %s returns " % dp, read(dp))
        #time.sleep(10)
        print ("-------------------------------------------------")
        break

    while 0:
        dp=hmAddress + "/NEQ1489656"
        print ("")
        print("read %s returns " % dp, read(dp))
        print ("-------------------------------------------------")
        dp=hmAddress + "/LEQ1259150"
        print ("")
        print("read %s returns " % dp, read(dp))
        print ("-------------------------------------------------")
        break
        
    while 0:
        dp=hmAddress + "/NEQ1489656/4"
        print ("")
        print("read %s returns " % dp, read(dp))
        #time.sleep(10)
        print ("-------------------------------------------------")
        break
        
    while 0:
        dp=hmAddress + "/NEQ1489656/4/ACTUAL_TEMPERATURE"
        print ("")
        print("read %s returns " % dp, read(dp))
        #time.sleep(10)
        print ("-------------------------------------------------")
        break
        

        
    while 0:   
        # print list of available parameters.
        print ("hommatic is ", hmAddress)
        ccu = pmatic.CCU (address=hmAddress, credentials=("Admin", ""))
        for x in ccu.devices.addresses():
           print (x, ccu.devices.get(x).name, ccu.devices.get(x).summary_state)
        time.sleep(3)


if __name__ == '__main__':
  main()

