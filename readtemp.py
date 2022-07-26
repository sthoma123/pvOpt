#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#28-00042b8679ff  28-00042b868bff  28-00042d9aabff  28-00042d9bdaff  28-00042d9cc1ff 
print ("imported " + __name__)

import os, glob, time, sys, datetime
import globals
import config
import metadata
import logging

import dpLogger

#initiate the temperature sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')


#----------------------------------------------------------------------------------------------------
def read_temp_raw(device_file): #a function that grabs the raw temperature data from the sensor
    f_1 = open(device_file, 'r')
    lines_1 = f_1.readlines()
    f_1.close()
    return lines_1


#----------------------------------------------------------------------------------------------------
#a function that checks that the connection was good and strips out the temperature
def read_temp(devicename): 
    logBuffer=[]
    
    device_file = '/sys/bus/w1/devices/28-' + devicename + '/w1_slave'
    try:
        rv = metadata.read("TEMP/" + devicename, "TEMP/" + devicename)

        lines = read_temp_raw(device_file)
        s="<br>".join(lines)
        dpLogger.log(logBuffer, "readTemp", "read %s got: %s" %(devicename, s))
        n = 0

        while (lines[0].strip()[-3:] != 'YES') and (n < 100):
        
            time.sleep(0.2)
            lines = read_temp_raw(device_file)
            n += 1
            
            s="<br>".join(lines)
            dpLogger.log(logBuffer, "EXCEPTION", "readTemp: read %s retry %d: %s" %(devicename, n, s))
             
        if n == 100:
            dpLogger.log(logBuffer, "EXCEPTION", 'readTemp: unable to read temperature; CRC-ERROR for ' + devicename)
            #return devicename, -99.9, "CRC Error" , datetime.datetime.now(), "TEMP/%s" % devicename, "CRC-Error" 
            rv [5] = "CRC-ERROR"
            dpLogger.flushLog("TEMP/" + devicename,logBuffer)
            return rv
    except IOError as e:
        s='unable to open file ' + device_file + ' for reading'
        dpLogger.log(logBuffer, "EXCEPTION", 'readTemp IOError %s' % s)
        
        s="I/O error({0}): {1}".format(e.errno, e.strerror)
        dpLogger.log(logBuffer, "EXCEPTION", 'readTemp IOError %s' % s)
        #return devicename, -99.9, "wrong" , datetime.datetime.now(), "TEMP/%s" % devicename, e.strerror 
        rv [5] = "Exception %s" % e.strerror
        logging.exception("readtemp.py")
        
        dpLogger.flushLog("TEMP/" + devicename,logBuffer)
        return rv

    
    equals_pos = lines[1].find('t=')
    temp = float(lines[1][equals_pos+2:])/1000
    
    #translatedDevicename="TEMP/%s" % devicename   #default name
    #if devicename in globals.config.configMap["Tempsensors"]:
    #   translatedDevicename=globals.config.configMap["Tempsensors"][devicename]
    # rv = translatedDevicename, temp, "Grad", datetime.datetime.now(), "TEMP/%s" % devicename, "Ok"
    
    rv[1] = temp
    rv [5] = "Ok"
    
    dpLogger.flushLog("TEMP/" + devicename,logBuffer)
    return rv

#----------------------------------------------------------------------------------------------------
# read takes defined datapoint syntax:
# takes list or string: BOX/ID/SUBID/SUBSUBID
# box is ignored # // important for archive server und für gateways
# returns list: Name, Value, Unit, timestamp
def read(dp):

    rv = None
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    while len(dpList) < 2:  # brauche zumindest 2 elemente, auch wenn sie leer sind!
        dpList = [""] + dpList
        
    if dpList[1] == "":  
        rv = None  # default gibts kan
    else:
        rv = read_temp(dpList[1])

    return rv
#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
    globals.config= configuration

    devicenames = [s.split('-')[1] for s in glob.glob('/sys/bus/w1/devices/28*')]
    
    print ("Available devices: ")
    for device in devicenames:
        s=metadata.read("TEMP/%s" % device, "metadata: unknown Temperature sensor")
        print ("   TEMP/%s: %s" % (device, s[0]))
    print ("")
      
    
    while 1:
        #p = [read_temp(devicename) for devicename in globals.config.configMap["Tempsensors"]]
        p = [read_temp(devicename) for devicename in devicenames]
        s=[(pp[0] + ": " + str(pp[1]) + " " + pp[2] + repr(pp)) for pp in p]
        print (str(datetime.datetime.now()), " ".join(s))

    ###    print (str(datetime.datetime.now()) + ' temps are ' + " ".join(map(str, temp)))
        break
        time.sleep(3)
