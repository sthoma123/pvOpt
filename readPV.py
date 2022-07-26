#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß

#  for Fronius Symo
#
#
#  161130 only return float or string.
#  201015 check error codes from PV.  
#
#
#
#
print ("imported " + __name__)

import os, glob, time, sys, datetime
import http, http.client
import json
import config
import globals
from funcLog import logged
import logging
import dpLogger


#gDevicenames = ["PV0", "PV1"]
#reads the both PVs
##config=json.load(open("/opt/pvOpt/config.json"))
logBuffer=[]
froniusCode={
"0" : "Ok",
"102": "AC voltage too high",
"103": "AC voltage too low",
"105": "AC frequency too high",
"106": "AC frequency too low",
"107": "No AC grid detected / Wrong AC Grid State detected",
"108": "Islanding detected",
"112": "Residual Current Detected",
"140": "ERR_OVPEN",
"212": "AC voltage L1-N too high",
"213": "AC voltage L1-N too low",
"222": "AC voltage L2-N too high",
"223": "AC voltage L2-N too low",
"232": "AC voltage L3-N too high",
"233": "AC Voltage L3-N too low",
"240": "Arc Detected",
"241": "Arc detection confirmation 1",
"242": "Arc detection confirmation 2",
"243": "Arc Detected - Detected Arc does not fullfill the standardized AFCI switch-off limits",
"245": "Arc Fault Cicruit Interrupter (AFCI) Selftest failed",
"247": "Arc Fault Cicruit Interrupter (AFCI) current sensor error",
"249": "Arc Fault Cicruit Interrupter (AFCI) detected unplausibel measurement values",
"301": "AC Overcurrent",
"302": "DC Overcurrent",
"303": "Channel 1 Overtemperature",
"304": "Channel 2 Overtemperature",
"305": "Intermediate Circute Undervoltage",
"306": "DC/AC Power Low",
"307": "DC Voltage Low",
"308": "Intermediate Circute Overvoltage",
"309": "DC1 Input Overvoltage",
"311": "DC Poles Reversed",
"312": "Ambient Temperature Too Low",
"313": "DC2 Input Overvoltage",
"314": "DC System Failure",
"315": "Current Sensor Error",
"316": "Filter Interrupt Timing Error",
"323": "Snubber Overvoltage",
"324": "Channel 3 Overtemperature",
"325": "Channel 4 Overtemperature",
"326": "Fan 1 Error",
"327": "Fan 2 Error",
"401": "Power Stack Communication Error ·",
"406": "Channel 1 Sensor Error",
"407": "Channel 2 Sensor Error",
"408": "DC In Public Power Grid",
"412": "DC1 Fix Voltage Out Of Range",
"415": "Wired Shutdown Triggered",
"416": "ReCerbo - Power Stack Communication Error",
"417": "Hardware-ID Collision",
"419": "ERR_UnUNIDDetected",
"420": "Hardware-ID Collision",
"421": "ERR_HIDRange",
"425": "Data Exchange Timeout",
"426": "Intermediate Circute Loading Timeout",
"427": "Power Stack Ready Timeout",
"428": "ERR_WaitPSAttach",
"429": "ERR_WaitPSDetach",
"431": "Power Stack In Bootmode",
"432": "Consistent error in power stack management",
"433": "Allocation error of dynamic addresses",
"436": "Invalid Bitmap Received",
"437": "Power Stack Event Handling Error",
"438": "Problem while error transmission from power stack to display board",
"442": "ERR_PSMissingInPhase",
"443": "DC/DC energy transfer failure",
"445": "Invalid Configuration",
"447": "Isolation Error",
"448": "No Neutral Wire",
"450": "Guard Communication Error",
"451": "Memory Check Error",
"452": "Power Stack - Filter Communication Error",
"453": "Guard UAC Error",
"454": "Guard fAC Error",
"456": "Guard Anti Islanding Selftest Error",
"457": "Grid Relay Sticks",
"458": "Residual Current Monitoring Unit Offset Error",
"459": "Guard Isolation Selftest Error",
"460": "Power Stack/Filter Print Reference Voltage Error",
"461": "RAM Error / Collective Fault",
"462": "Guard DC In Public Power Grid Selftest Error",
"463": "AC Poles Reversed",
"471": "Ground Missing",
"472": "Ground-Fault Detector Interrupter Fuse Broken",
"474": "Residual Current Sensor Broken",
"475": "Isolation Too Low Error",
"476": "Power Stack Supply Missing",
"480": "Compulsive Feature Incompatible",
"481": "Compulsive Feature Not Supported",
"482": "Installation Wizzard Aborted",
"483": "DC2 Fix Voltage Out Of Range",
"484": "CAN Transfair Timeout",
"485": "CAN Transmit Buffer Full",
"502": "Isolation Too Low Warning",
"509": "No Feed In For 24Hrs",
"515": "Communication with string monitoring not possible ·",
"516": "Power Stack EEPROM Error",
"517": "Overtemperature Dependent Power Derating ·",
"518": "Power stack Derating caused by too high temperature",
"519": "Filter Print EEPROM Error",
"520": "No Feed In For 24Hrs MPPT1",
"521": "No Feed In For 24Hrs MPPT2",
"522": "DC1 Input Voltage Low",
"523": "DC2 Input Voltage Low",
"551": "Ground Missing ·",
"558": "Incompatible Power stack Feature",
"559": "Incompatible ReCerbo Feature",
"560": "Grid Frequency Dependent Power Derating",
"565": "Arc Fault Cicruit Interrupter SD Card Error",
"566": "Arc Fault Cicruit Interrupter Deactivated Warning",
"567": "Arc Fault Cicruit Interrupter SD Card Error",
"568": "Arc Fault Cicruit Interrupter Deactivated Warning",
"571": "Grid Voltage Dependent Power Derating",
"572": "External I/O Warning",
"573": "Software State Inconsistency",
"574": "Power Limit Invalid",
"579": "Developer Warning",
"601": "CAN Bus Full",
"602": "Blocked By Italy Autotest",
"603": "Channel 3 Sensor Error",
"604": "Channel 4 Sensor Error",
"605": "Isolation Controller Communication Error",
"606": "Isolation Controller Supply Missing",
"607": "RCMU Continous Fault",
"608": "Power Stack Software Incompatibility",
"609": "Configuration Value Out Of Limits",
"668": "External I/O Error ·",
"701": "LocalNet - Node Type Out Of Range",
"702": "LocalNet - Receive Buffer Full",
"703": "LocalNet - Send Buffer Full",
"705": "LocalNet - Node Type Conflict",
"706": "CapKey - Get Version Failed",
"707": "CapKey - Update Failed",
"708": "CapKey - Reserved 1",
"709": "CapKey - Reserved 2",
"711": "EEPROM Write - Wrong Data Length",
"712": "EEPROM Write - Descriptor Not Found",
"713": "EEPROM Read - Descriptor Not Found",
"714": "EEPROM Read Warning - CRC Header Fail Will Retry",
"715": "EEPROM Read - CRC Header Fail Give It Up",
"721": "EEPROM - Reinitialized",
"722": "EEPROM - Wait Busy Timeout",
"723": "EEPROM Write - Verify Fail Will Retry",
"724": "EEPROM Write - Verify Fail Give It Up",
"725": "EEPROM Read - CRC Data Fail Will Retry",
"726": "EEPROM Read - CRC Data Fail Give It Up",
"727": "EEPROM Check Data Warning - All Data Corrupt",
"730": "EEPROM Check Data - Data Restored",
"731": "USB Initializing Error",
"732": "USB Overcurrent",
"733": "No USB Stick Inserted",
"734": "No Update File Found On USB Stick",
"735": "Not Supported Update File Found On USB Stick",
"736": "USB Read/Write Error",
"737": "Update File Can Not Be Read",
"738": "Log-File Can't Be Created",
"740": "USB Enumeration Error",
"741": "USB Logging Write Error",
"743": "Update Failed",
"745": "Update File Checksum Wrong",
"746": "PMC Read Error While Update",
"751": "RTC Time Lost",
"752": "RTC Hardware Error",
"754": "RTC Time Set",
"755": "EEPROM Data Written",
"757": "RTC Hardware Error",
"758": "RTC In Emergency Mode",
"760": "System Crystal Broken",
"761": "Onboard Memory PCB Read Error",
"762": "Plugged Memory PCB Read Error",
"765": "Random Number Generator Error",
"766": "Power Limit Not Found",
"767": "Power Limiter Communication Error",
"768": "Power Limit Not Identical",
"772": "Memory Not Available",
"773": "Update Group Zero",
"775": "Power Stack Product Matrix Code Invalid",
"777": "CAN Error Message Source",
"778": "CAN Error Message Statecode",
"782": "Update Flash - CRC Error",
"783": "Update Flash - Header CRC Error",
"784": "Update Flash - Timeout",
"785": "Update Flash - Read Value (Value Not Found)",
"787": "Update Flash - Read Value (Setup Not Found)",
"789": "Update Flash - Read Value (Header CRC Error)",
"792": "Update Flash - Find Header (Header Not Found)",
"794": "Update Flash - Find Header (Header Address Impossible)"
}



#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read_pv_raw(wechselrichter): #network name of device
    global logBuffer

    try:
        connection = http.client.HTTPConnection(wechselrichter, timeout=10)
        connection.request('GET', '/solar_api/v1/GetInverterRealtimeData.cgi?Scope=Device&DeviceId=1&DataCollection=CommonInverterData')
        response = connection.getresponse()
        cont = response.read().decode()
        s = "read from %s got %s " % (wechselrichter, str(cont))
        dpLogger.log(logBuffer, "readPV", s)
    except Exception as e:
        s = "readpv Exception while reading from %s Exception %s, %s" % (wechselrichter, type(e).__name__, str(e))
        dpLogger.log(logBuffer, "EXCEPTION", s)
        #print ('unable to retrieve data from ' + wechselrichter)
        #print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
        return None
        
    return cont



#----------------------------------------------------------------------------------------------------
#a function that checks that the connection was good and strips out the temperature
@logged(logging.DEBUG)
def read_pv(wechselrichter, parameter): 
    
    global logBuffer
    rv= None

    response = globals.cache.get(wechselrichter, read_pv_raw, 10)        
            
    try:
        if response is None:  # WR hat nicht geantwortet!
            rv = "%s of %s" %(parameter, wechselrichter), 0.0, "~" , datetime.datetime.now()  , "PV/%s/%s" %(wechselrichter, parameter), "Timeout"
            dpLogger.log(logBuffer, "readPV", "timeout")
        elif len(response) < 20:   #seems reasonable length
            rv = "%s of %s" %(parameter, wechselrichter), 0.0, "~" , datetime.datetime.now()  , "PV/%s/%s" %(wechselrichter, parameter), " short Response"
            dpLogger.log(logBuffer, "readPV", "response too short %d" % len(response))
        else:
            r = json.loads(response)["Body"]["Data"]
            errorMsg=""
            
            try:
                errorCode=0
                if "DeviceStatus" in r:
                    if "ErrorCode" in r["DeviceStatus"]:
                        errorCode = r["DeviceStatus"]["ErrorCode"]
                        errorMsg="Fronius Code %s" % (str(errorCode))
                        if str(errorCode) in froniusCode:
                            errorMsg="Fronius Code %s: %s" % (str(errorCode), froniusCode[str(errorCode)])
                            
                        dpLogger.log(logBuffer, "readPV", "%s for %s %s" % (errorMsg, parameter, wechselrichter))
                        errorMsg=" (%s)" % errorMsg     #format to append to readable dpname
                
                val = r[parameter]["Value"]
                                            
                if type(val) is int:
                    val = float(val)
                    
                
                rv = ("%s of %s%s" %(parameter, wechselrichter, errorMsg), val, 
                    r[parameter]["Unit"],  
                    datetime.datetime.fromtimestamp(globals.cache.getStamp(wechselrichter)) ,
                    "PV/%s/%s" %(wechselrichter, parameter),
                    "Ok")
            except KeyError as e: # ignorieren, wechselrichter antworten nicht.
                rv= "%s of %s%s" %(parameter, wechselrichter, errorMsg), 0.0, "W" , datetime.datetime.now() , "PV/%s/%s" %(wechselrichter, parameter), "Exception"
                dpLogger.log(logBuffer, "readPV", "keyError: Body.Data.%s.Value or .Unit" % parameter)

                    
    except Exception as e:
        #print ("read_pv: exception: %s/%s: %s" %(wechselrichter, parameter, str(e)))
        #print (type(e))
        #print ('got wrong response from (no json body,data)' + wechselrichter)
        #print (response)
         #   print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
        logging.exception ( "unable to read %s from %s" % (parameter, wechselrichter))
        rv= "%s of %s" %(parameter, wechselrichter), 0, "W" , datetime.datetime.now() , "PV/%s/%s" %(wechselrichter, parameter), "Exception"

    if len (logBuffer) > 0:
        dpLogger.flushLog("PV/%s/%s" %(wechselrichter, parameter), logBuffer)
        logBuffer = []

    return rv    

#----------------------------------------------------------------------------------------------------
# getTotalPAC:
#

def getTotalPAC():
    
    parameter= "PAC"
    p= [read_pv(wechselrichter, parameter) for wechselrichter in globals.config.configMap["Devicenames"]]
    if p[0] is not None and p[1] is not None:
        s=[(pp[0] + ": " + str(pp[1]) + " " + pp[2]) for pp in p]
#        print (str(datetime.datetime.now()), " ".join(s), "total: " , str(p[0][1] + p[1][1]) + " " + p[0][2])
    rv = 0
    if p[0] is not None:
       rv+=p[0][1]
    if p[1] is not None:
       rv+=p[1][1]
    return rv

#----------------------------------------------------------------------------------------------------
# getList:
#   gets a plain list of defined variables
#   dp is a part of the datapoint (e.g. the first part of the datapoint)
#
@logged(logging.DEBUG)
def getList(dp):
# todo only return those starting with dp
    rv = "PAC", 
    return rv

#----------------------------------------------------------------------------------------------------
# read takes defined datapoint syntax:
# takes list or string: /box/ID/SUBID/SUBSUBID
# returns list: Name, Value, Unit, timestamp
def read(dp):

    rv = None
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    while len(dpList) < 2:  # brauche zuminest 2 elemente, auch wenn sie leer sind!
        dpList += [""]
        
    if dpList[1] == "":
       dpList[1] = "PAC"
       
    if dpList[0] == "":  # summe aus allen vorhandenen
        dpls = [[dev] + dpList[1:] for dev in globals.config.configMap[Devicenames]]  
        #print("dpls=", dpls)
        valuelists=[read(dpl) for dpl in dpls]
        #print("values=", values)
        v= [0 if x is None else x[1] for x in valuelists]
        rv = "Total", sum(v), "Watt", datetime.datetime.now(), valuelists[0][4], valuelists[0][5]
    else:
        rv = read_pv(dpList[0], dpList[1])

    return rv

#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
    globals.config= configuration
    # print list of available parameters.
    wechselrichter = globals.config.configMap["Devicenames"][0] # take first available...
    response = globals.cache.get(wechselrichter, read_pv_raw, 10)
    if not response is None and  (len(response) > 20):   #seems reasonable length
        print ("got response JSON string: " + response)
        r = json.loads(response)["Body"]["Data"]
        print ("data parameter list is :" + str(r.keys()))
    else:
        print ("got no reposnse from " + wechselrichter)
    

    parameter= "PAC"
    while 1:
        print ("Devicenames are %s" % str(globals.config.configMap["Devicenames"]))
        p= [read_pv(wechselrichter, parameter) for wechselrichter in globals.config.configMap["Devicenames"]]
        
        try:
            s=[(pp[0] + ": " + str(pp[1]) + " " + pp[2]) for pp in p]
            print (str(datetime.datetime.now()), " ".join(s), "total: " , str(p[0][1] + p[1][1]) + " " + p[0][2])
        except:
            print ('got wrong response from read_pv')
            print (p)

        time.sleep(3)

