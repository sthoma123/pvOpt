#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß

#  for BatterX system
#
#  
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
import JSONHelper


logBuffer=[]

#
# 
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read_bx_raw(wechselrichter, url='/api.php?get=currentstate'): #network name of device
    global logBuffer

    try:
        connection = http.client.HTTPConnection(wechselrichter, timeout=10)
        connection.request('GET', url)

        response = connection.getresponse()
        cont = response.read().decode()  #converts byte array to string (json)
        #cont = JSONHelper._decode(cont)
        s = "read_bx_raw %s from %s got %s " % (url, wechselrichter, str(cont))
        print(s)
        dpLogger.log(logBuffer, "readBX", s)
        
    except Exception as e:
        s = "readBX Exception while reading from %s Exception %s, %s" % (wechselrichter, type(e).__name__, str(e))
        dpLogger.log(logBuffer, "EXCEPTION", s)
        logging.exception(s)
        print (s)
        #print ('unable to retrieve data from ' + wechselrichter)
        #print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
        return None
        
    return cont

PARMMAPPING = { # to be backward compatible
     "PAC" : "1634",
     "PBATT" : "1121",
     "GRIDPOWER" : "2913"
     }

PARMIDS = {
#{id: [mnemonic, entity, longtext, multiplikator, unit], ... }
     
    "273" : 	  ["V1", "1", "Input Voltage L1", 1/100, "V"],
    "274" : 	  ["V2", "1", "Input Voltage L2", 1/100, "V"],
    "275" : 	  ["V3", "1", "Input Voltage L3", 1/100, "V"],					
    "305" : 	  ["", "1", "Input Current L1", 1/100, "A"],
    "306" : 	  ["", "1", "Input Current L2", 1/100, "A"],					
    "307" : 	  ["", "1", "Input Current L3", 1/100, "A"],					
    "337" : 	  ["", "1", "Input Power L1", 1, "W"],
    "338" : 	  ["", "1", "Input Power L2", 1, "W"],
    "339" : 	  ["", "1", "Input Power L3", 1, "W"],
    "353" : 	  ["", "1", "Input Power Total", 1, "W"],
    "354" : 	  ["", "1", "Input Frequency", 1/100, "Hz"],
    "369" : 	  ["", "1", "Internal Temp", 1, "°C"],
    #"1041" :     ["", "1", "Battery Voltage Minus-N", 1/100, "V"],
    "1042" : 	 ["", "1", "Battery Voltage", 1/100, "V"],
    "1058" : 	 ["", "1", "Battery Current", 1/100, "A"],
    "1074" : 	 ["", "1", "Battery Capacity", 1, "%"],
    "1121" : 	 ["PBATT", "1", "Battery Power Total", 1, "W"],
    
    "1297" : 	 ["", "1", "Protected Voltage L1", 1/100, "V"],
    "1298" : 	 ["", "1", "Protected Voltage L2", 1/100, "V"],
    "1299" : 	 ["", "1", "Protected Voltage L3", 1/100, "V"],
    "1329" : 	 ["", "1", "Protected Current L1", 1/100, "A"],
    "1330" : 	 ["", "1", "Protected Current L2", 1/100, "A"],
    "1331" : 	 ["", "1", "Protected Current L3", 1/100, "A"],
    "1361" : 	 ["", "1", "Protected Power L1", 1, "W"],
    "1362" : 	 ["", "1", "Protected Power L2", 1, "W"],
    "1363" : 	 ["", "1", "Protected Power L3", 1, "W"],
    "1377" : 	 ["", "1", "Protected Power Total", 1, "W"],
    "1378" : 	 ["", "1", "Protected Frequency", 1/100, "Hz"],
    "1553" : 	 ["", "1", "Solar Voltage 1", 1/100, "V"],
    "1554" : 	 ["", "1", "Solar Voltage 2", 1/100, "V"],

    "1569" : 	 ["", "1", "Solar Current 1", 1/100, "A"],
    "1570" : 	 ["", "1", "Solar Current 2", 1/100, "A"],
    
    "1617" : 	 ["", "1", "Solar Power 1", 1, "W"],
    "1618" : 	 ["", "1", "Solar Power 2", 1, "W"],	
    "1634" :     ["PAC", "0", "PV Power", 1, "W"],
    
    "2321/1" : 	 ["", "1", "Input 1 State", 1, ""],
    "2321/2" : 	 ["", "2", "Input 2 State", 1, ""],
    "2321/3" : 	 ["", "3", "Input 3 State", 1, ""],
    "2321/4" : 	 ["", "4", "Input 4 State", 1, ""],
    
    "2337/1" : 	 ["", "1", "Output 1 State", 1, ""],
    "2337/2" : 	 ["", "2", "Output 2 State", 1, ""],
    "2337/3" : 	 ["", "3", "Output 3 State", 1, ""],
    "2337/4" : 	 ["", "4", "Output 4 State", 1, ""],
	
    "2465/1" : 	 ["", "1", "GridInjection State", 1, ""],    #		
    "2465/2" : 	 ["", "2", "BatteryCharging State", 1, ""],    #		
    "2465/3" : 	 ["", "3", "BatteryChargingAC State", 1, ""],    #		
    "2465/4" : 	 ["", "4", "BatteryDischarging State", 1, ""],    #		
    "2465/5" : 	 ["", "5", "BatteryDischargingAC State", 1, ""],    #		
   
    "2833" : 	 ["", "0", "Grid Voltage L1", 1/100, "V"],
    "2834" : 	 ["", "0", "Grid Voltage L2", 1/100, "V"],
    "2835" : 	 ["", "0", "Grid Voltage L3", 1/100, "V"],
    "2865" : 	 ["", "0", "Grid Current L1", 1/100, "A"],
    "2866" : 	 ["", "0", "Grid Current L2", 1/100, "A"],					
    "2867" : 	 ["", "0", "Grid Current L3", 1/100, "A"],
    "2897" : 	 ["", "0", "Grid Power L1", 1, "W"],
    "2898" : 	 ["", "0", "Grid Power L2", 1, "W"],  		#0,"3" 	0,"4" 	0},	
    "2899" : 	 ["", "0", "Grid Power L3", 1, "W"],   #"0" 		0,"3" 	0,"4" 	0},	
    "2913" : 	 ["GRIDPOWER", "0", "Grid Power Total", 1, "W"],   #		1,"3" 	0,"4" 	1,"5" 	0},
    "2897/2" : 	 ["", "2", "Unprotected Power L1", 1, "W"],
    "2898/2" : 	 ["", "2", "Unprotected Power L2", 1, "W"],  		#0,"3" 	0,"4" 	0},	
    "2899/2" : 	 ["", "2", "Unprotected Power L3", 1, "W"],   #"0" 		0,"3" 	0,"4" 	0},	
    "2913/2" : 	 ["UNPROTPOWER", "2", "Unprotected Power Total", 1, "W"],   #		1,"3" 	0,"4" 	1,"5" 	0},
    "24582" : 	 ["", "1", "WinterCharge Status", 1, "s"],
    "28417" : 	 ["", "1", "Max AC Charging Current", 1/100, "A"]
     }

PARMIDSHISTORY = {
        0: ["LOGTIME", "timestamp", 1, "s"],
        1: ["BATTERY_VOLTAGE_MINUS", "Battery voltage of the Minus side of the battery", 1/100, "V"],
        2: ["BATTERY_VOLTAGE_PLUS", "Battery voltage of the Plus side of the battery", 1/100, "V"],
        3: ["BATTERY_LEVEL_MINUS", "Battery Level of the minus side of the battery", 1, "%"],
        4: ["BATTERY_LEVEL_PLUS", "Battery level of the plus side of the battery", 1, "%"],
        5: ["BATTERY_POWER_FROM", "Battery discharging power", 1, "W"],
        6: ["BATTERY_POWER_TO", "Battery charging power", 1, "W"],
        7: ["INPUT_POWER_FROM", "Power imported from the input of the UPS", 1, "W"],
        8: ["INPUT_POWER_TO", "Power exported to the input of the UPS", 1, "W"],
        9: ["GRID_POWER_FROM", "Power imported from the grid, measured by Energy Meter EM0", 1, "W"],
        10: ["GRID_POWER_TO", "Power exported to the grid, measured by Energy Meter EM0", 1, "W"],
        11: ["LOAD_POWER", "Power of the protected output", 1, "W"],
        12: ["HOUSE_POWER", "Power of the unprotected load", 1, "W"],
        13: ["SOLAR_POWER", "Solar power of the UPS", 1, "W"],
        14: ["EXTSOL_POWER", "Solar power of the external solar devices, measured by Energy Meter EM3", 1, "W"]
    }
    
PARMIDSWARNINGS = {
        16640: "Grid Loss",
        16641: "Island",
        16642: "Grid Phase Dislocation",
        16643: "Grid Wave Loss",
        16644: "Grid Ground Loss",
        16657: "Grid Voltage Loss",
        16658: "Grid Voltage High Loss",
        16659: "Grid Voltage Low Loss",
        16660: "Grid Average Voltage Over",
        16738: "Grid Frequency Loss",
        16739: "Grid Frequency High Loss",
        16740: "Grid Frequency Low Loss",
        17665: "Output Short",
        17682: "Output Voltage High Loss",
        17683: "Output Voltage Low Loss",
        17761: "Output Overload Fault",
        17762: "Output Overload Fault L1",
        17763: "Output Overload Fault L2",
        17764: "Output Overload Fault L3",
        17765: "Output Overload Warning",
        17766: "Output Overload Warning L1",
        17767: "Output Overload Warning L2",
        17768: "Output Overload Warning L3",
        17408: "Battery Open",
        17425: "Battery Voltage Too High",
        17426: "Battery Low",
        17427: "Battery Under",
        17441: "Battery Weak",
        17442: "Battery Discharge Low",
        17443: "Battery Low in Hybrid Mode",
        17444: "Battery Over Charge",
        17457: "Battery Over Current",
        17920: "Solar Loss",
        17921: "Solar Input 1 Loss",
        17922: "Solar Input 2 Loss",
        17929: "Solar Input Short",
        17937: "Solar Voltage Too High",
        17938: "Solar Voltage Too Low",
        17953: "Solar Input 1 Voltage Too High",
        17954: "Solar Input 2 Voltage Too High",
        17969: "Solar Over Current",
        18017: "Solar Input Power Abnormal",
        18065: "Solar Insulation Fault",
        17152: "Bus Soft Start Timeout",
        17169: "Bus Over Voltage",
        17170: "Bus Under Voltage",
        18176: "Inverter Soft Start Timeout",
        18177: "Inverter Relay Fault",
        18225: "Inverter Current Too High",
        18226: "Inverter Over Current For Long Time",
        18689: "Over Temperature",
        18690: "Control Board Wiring Error",
        18691: "External Flash Fail",
        18692: "Initial Fail",
        18693: "Fan Stop",
        18694: "EPO Active",
        18696: "DC Current Sensor Fail",
        18697: "Power Down",
        18704: "Leakage current too high",
        18705: "Leakage current sensor fault",
        18706: "Line value consistent fail between MCU & DSP",
        18707: "Connect fail between MCU & DSP",
        18708: "Communication fail between MCU & DSP",
        18709: "Current Sensor Fault",
        18710: "Discharge Fail",
        18711: "Discharge Soft Time Out",
        18712: "SPS Power Voltage Abnormal",
        18713: "AC Circuit Voltage Sample Error",
        18912: "CliX  - Automatic Bypass ON",
        18913: "CliX  - Overload in Battery Mode, Output OFF",
        18928: "LiveX - Energy Meter Not Working"
}


#-----------------------------------------------------------------------------------------------
#returns data in the list format:
#    rv={"info": driverCommon.getInfoArchive(dp),
#        "header": ["timestamp", "thread", "topic", "message"], 
#        "data":data}
#    
def read_bx_warn(wechselrichter, fromdate=None):
    global logBuffer

    rv = {};
    rv["info"]="Warnings of BX %s from %s" % (wechselrichter, fromdate)
    rv["header"]=["timestamp", "id", "message"]
    rv["data"]=["no data"]
    
    ##http://192.168.0.173/api.php?get=warnings&from=20191014
    if fromdate is None or fromdate == "":
        response = read_bx_raw(wechselrichter, '/api.php?get=warnings')
    else:
        response = read_bx_raw(wechselrichter, '/api.php?get=warning&from=%s' % fromdate)
        
    print ("0 bx returned %s (type %s)" %(str(response), str(type(response))))
    if response is not None:
        r = JSONHelper._decode(response)  #also handles datetime
        #print ("1 bx returned %s (type %s)" %(str(r), str(type(r))))
        #[["2020-02-03 19:18:12",[]]]
        #[["2019-10-14 10:27:35",[17921,17408,17443,18928]],["2019-10-14 11:28:19",[]],["2019-10-14 12:13:33",[18918]]]
        try:
            rv["data"]=[]
            if len(response)>0:
                for rr in response:
                    if len(rr) > 0:
                        timestamp = rr[0]  #warning: GMT!!!
                        if len(rr)>1:
                            for rrr in rr[1]:
                                rv[data].append([timestamp, rrr, PARMIDSWARNINGS[rrr]])
                    
        except Exception as e:
            s = "read_bx Exception while reading warnings from %s Exception %s, %s" % (wechselrichter, type(e).__name__, str(e))
            dpLogger.log(logBuffer, "EXCEPTION", s)
            print (s)
            logging.exception (s)
            rv ["data"] = s
            
    return rv
    
def read_bx_history(wechselrichter, fromdate, todate):

    returnread_bx_raw(wechselrichter, '/api.php?get=history&from=%s&to=%s'%(fromdate, todate))
                  
#-----------------------------------------------------------------------------------------------
def read_bx_warnings(wechselrichter, fromdate, todate):
    global logBuffer

    if fromdate is None:
        fromdate = ""
    if todate is None:
        todate = ""
        
    
    val = read_bx_warn(wechselrichter, fromdate)
    
    rv = "%s of %s" %("Warnings", wechselrichter), val, "" , datetime.datetime.now()  , "BX/%s/%s" %(wechselrichter, "WARNINGS"), "Ok"
    
    return rv


#----------------------------------------------------------------------------------------------------
#a function that checks that the connection was good and strips out the temperature
@logged(logging.DEBUG)
def read_bx(wechselrichter, pa, ent): 
    
    global logBuffer
    rv= None
    parameter = pa
    if ent != "":
        parameter += "/" + ent

    #rv= "%s of %s" %(parameter, wechselrichter), 0, "~" , datetime.datetime.now() , "BX/%s/%s" %(wechselrichter, pa), "Exception"
    #rv = metadata.read("MQTT/" + dp, "MQTT/" + dp)    

    
    if parameter not in PARMIDS:
        if parameter in PARMMAPPING:
            parameter = PARMMAPPING[parameter]
        else:
            parameter = ""
            dpLogger.log(logBuffer, "readBX", "unknown parameter for BX: %s " % pa)
            
    if parameter in PARMIDS:
        paID = PARMIDS[parameter]

        response = globals.cache.get(wechselrichter, read_bx_raw, 5)
                
        try:
            if response is None:  # WR hat nicht geantwortet!
                rv = "%s of %s" %(parameter, wechselrichter), 0.0, "W" , datetime.datetime.now()  , "BX/%s/%s/%s" %(wechselrichter, parameter, ent), "Timeout"
                dpLogger.log(logBuffer, "readBX", "timeout")                
                print ("readBX: timeout")
            else:

                if len(response) > 20:   #seems reasonable length
    #{"273":{"1":22980},"logtime":"2020-01-31 13:43:26","305":{"1":182},"337":{"1":419},"274":{"1":23330},"306":{"1":-85},"338":{"1":-200},"275":{"1":23160},"307":{"1":-136},"339":{"1":-317},"353":{"1":-98},"354":{"1":4998},"369":{"1":26},"2833":{"0":23016},"2865":{"0":199},"2897":{"0":458,"2":39},"2834":{"0":23358},"2866":{"0":-80},"2898":{"0":-186,"2":13},"2835":{"0":23051},"2867":{"0":-119},"2899":{"0":-274,"2":42},"2913":{"0":-2,"2":95},"1297":{"1":22960},"1329":{"1":357},"1361":{"1":821},"1298":{"1":23350},"1330":{"1":85},"1362":{"1":199},"1299":{"1":23160},"1331":{"1":34},"1363":{"1":81},"1377":{"1":1101},"1378":{"1":5000},"1042":{"1":4870},"1058":{"1":-2030},"1074":{"1":30},"1121":{"1":-988},"1553":{"1":34950},"1569":{"1":18},"1617":{"1":63},"1554":{"1":34990},"1570":{"1":21},"1618":{"1":75},"1634":{"0":138},"2321":{"1":0,"2":0,"3":0,"4":0},"2337":{"1":0,"2":0,"3":0,"4":0},"2465":{"1":1,"2":1,"3":0,"4":1,"5":0},"24582":{"1":1540684},"28417":{"1":14800}}            
                    #r = json.loads(response)
                    #print ("read_bx got %s" % response)
                    r = JSONHelper._decode(response)  #also handles datetime
                    #print ("read_bx converted to %s" % str(r))
                    try:
                        mnemonic, entity, desc, multipl, unit = PARMIDS[parameter]
                        if "logtime" in r:
                            logtime = r["logtime"]  # warning, this is GMT!!!
                        else:
                            dpLogger.log(logBuffer, "readBX", "Warning: response from BX did not contain logtime: %s" %(str(r)))
                            logtime = datetime.datetime.now()
                        
                        data = r[parameter.split("/")[0]]
                        val = data[entity]  #sometimes there are more entities per parameter, currently I don't know the reason. just take the configured one...
                        
                        if type(val) is int:
                            val = float(val)
                        if type(val) is float:
                            val = multipl * val
                        dp = "BX/%s/%s" %(wechselrichter, pa)
                        if ent != "":
                            dp += "/" + ent
                            
                        rv = (desc, val, unit, logtime, dp, "Ok")
                        #datetime.datetime.fromtimestamp(globals.cache.getStamp(wechselrichter)) ,
                        
                    except KeyError as e: # ignorieren, wechselrichter antworten nicht.
                        logging.exception ( "read_BX: problem with BX/%s/%s" % (wechselrichter, pa))
                        
                        s= ("keyError %s for parm %s" % (str(e), parameter))
                        #rv= "%s of %s" %(parameter, wechselrichter), 0.0, "W" , datetime.datetime.now() , "BX/%s/%s" %(wechselrichter, pa), "Exception"
                        print (s)
                        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "BX/%s/%s" %(wechselrichter, pa), "Exception"
                        dpLogger.log(logBuffer, "EXCEPTION", s)
                        
        except Exception as e:
            #logging.exception ( "read_BX: problem with BX/%s/%s" % (wechselrichter, pa))
            #print ("read_bx: exception: %s/%s: %s" %(wechselrichter, parameter, str(e)))
            #print (type(e))
            #print ('got wrong response from (no json body,data)' + wechselrichter)
            #print (response)
            #print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
             
            s = "read_bx Exception while reading %s from %s Exception %s, %s" % (parameter, wechselrichter, type(e).__name__, str(e))
            dpLogger.log(logBuffer, "EXCEPTION", s)
            
            print (s)
            logging.exception (s)
            #rv= "%s of %s" %(parameter, wechselrichter), 0, "W" , datetime.datetime.now() , "BX/%s/%s" %(wechselrichter, pa), "Exception"
            rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "BX/%s/%s" %(wechselrichter, pa), "Exception"
            
        if len (logBuffer) > 0:
            dpLogger.flushLog("BX/%s/%s" %(wechselrichter, parameter), logBuffer)
            logBuffer = []

    return rv    


#----------------------------------------------------------------------------------------------------
# 
def getLog(wechselrichter, fromdate=None):
    return read_bx_warn(wechselrichter, fromdate)

#----------------------------------------------------------------------------------------------------
# read takes defined datapoint syntax:
# takes list or string: /box/ID/SUBID/SUBSUBID
# returns list: Name, Value, Unit, timestamp
def read(dp):

    global logBuffer

    rv = None
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    while len(dpList) < 4:  # brauche zuminest 3 elemente, auch wenn sie leer sind!
        dpList += [""]
        
    rv = None
        
    if dpList[1] == "": #parm
       rv= "readBX: Exception: Parameter missing", 0, "~" , datetime.datetime.now() , "BX/%s" %(dp), "Exception"
       
    if dpList[0] == "": #bx box
       rv= "readBX: Exception: Parameter missing", 0, "~" , datetime.datetime.now() , "BX/%s" %(dp), "Exception"
       
    try:
        if rv is None:
            if dpList[1]=="WARNINGS":
                rv = read_bx_warnings(dpList[0], dpList[2], dpList[3]) #dpList[2] can be from-date...
            else:
                rv = read_bx(dpList[0], dpList[1], dpList[2])  #box/id/subid
            
    except Exception as e:
        s = "BX Exception while reading %s Exception %s, %s" % (dp, type(e).__name__, str(e))
        dpLogger.log(logBuffer, "EXCEPTION", s)            
        print (s)
        logging.exception (s)
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "BX/%s" %(dp), "Exception"
                        
    if len (logBuffer) > 0:
        dpLogger.flushLog("BX/%s" %(dp), logBuffer)
        logBuffer = []

    return rv

#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
    globals.config= configuration
    # print list of available parameters.
    
    wechselrichter = "192.168.0.173"
    response = globals.cache.get(wechselrichter, read_bx_raw, 10)
    if not response is None and  (len(response) > 20):   #seems reasonable length
        print ("got response JSON string: " + response)
        r = json.loads(response)
        print ("data parameter list is :" + str(r.keys()))
    else:
        print ("got no response from " + wechselrichter)
    

    #p = ["PAC", "GRIDPOWER"]
    p = PARMIDS.keys()
    while 1:     
        for pp in p:
            try:
                r = read(wechselrichter + "/" + pp)
                print ("got %s is %s: %s%s" % (pp, r[0], str(r[1]), r[2]))
                
                #print (str(r))
            except Exception as e:
                s="readBX: main: Exception for parm %s: %s" % (p, str(e))
                print(s)
                logging.exception(s)

        time.sleep(1)

