#!/usr/bin/python3

#
#  161130 only return float or string.
#
#
#
#
import os, glob, time, sys, datetime
import http, http.client
import json
import config
import globals
from funcLog import logged
import logging


#gDevicenames = ["PV0", "PV1"]
#reads the both PVs
##config=json.load(open("/opt/pvOpt/config.json"))

#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read_pv_raw(wechselrichter): #network name of device
    try:
        connection = http.client.HTTPConnection(wechselrichter, timeout=10)
        connection.request('GET', '/solar_api/v1/GetInverterRealtimeData.cgi?Scope=Device&DeviceId=1&DataCollection=CommonInverterData')
        response = connection.getresponse()
        cont = response.read().decode()
    except:
        #print ('unable to retrieve data from ' + wechselrichter)
        #print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
        return None
    return cont



#----------------------------------------------------------------------------------------------------
#a function that checks that the connection was good and strips out the temperature
@logged(logging.DEBUG)
def read_pv(wechselrichter, parameter): 
    rv= None

    response = globals.cache.get(wechselrichter, read_pv_raw, 10)        
            
    try:
        if response is None:  # WR hat nicht geantwortet!
            rv = "%s of %s" %(parameter, wechselrichter), 0.0, "W" , datetime.datetime.now()  , "PV/%s/%s" %(wechselrichter, parameter), "Timeout"
        else:
            if len(response) > 20:   #seems reasonable length
                r = json.loads(response)["Body"]["Data"]
                try:
                    val = r[parameter]["Value"]
                    if type(val) is int:
                        val = float(val)
                    
                    rv = ("%s of %s" %(parameter, wechselrichter), val, 
                        r[parameter]["Unit"],  
                        datetime.datetime.fromtimestamp(globals.cache.getStamp(wechselrichter)) ,
                        "PV/%s/%s" %(wechselrichter, parameter),
                        "Ok")
                except KeyError as e: # ignorieren, wechselrichter antworten nicht.
                    rv= "%s of %s" %(parameter, wechselrichter), 0.0, "W" , datetime.datetime.now() , "PV/%s/%s" %(wechselrichter, parameter), "Exception"
                    
    except Exception as e:
        #print ("read_pv: exception: %s/%s: %s" %(wechselrichter, parameter, str(e)))
        #print (type(e))
        #print ('got wrong response from (no json body,data)' + wechselrichter)
        #print (response)
         #   print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
        logging.exception ( "unable to read %s from %s" % (parameter, wechselrichter))
        rv= "%s of %s" %(parameter, wechselrichter), 0, "W" , datetime.datetime.now() , "PV/%s/%s" %(wechselrichter, parameter), "Exception"
    return rv    

#----------------------------------------------------------------------------------------------------
# getTotalPAC:
#

def getTotalPAC():
    
    parameter= "PAC"
    p= [read_pv(wechselrichter, parameter) for wechselrichter in globals.config.Devicenames]
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
        dpls = [[dev] + dpList[1:] for dev in globals.config.Devicenames]  
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
#    gConfig=configuration
    globals.config= configuration
    # print list of available parameters.
    wechselrichter = globals.config.Devicenames[0] # take first available...
    response = globals.cache.get(wechselrichter, read_pv_raw, 10)
    if not response is None and  (len(response) > 20):   #seems reasonable length
        print ("got response JSON string: " + response)
        r = json.loads(response)["Body"]["Data"]
        print ("data parameter list is :" + str(r.keys()))
    else:
        print ("got no reposnse from " + wechselrichter)
    

    parameter= "PAC"
    while 1:
        print ("Devicenames are %s" % str(globals.config.Devicenames))
        p= [read_pv(wechselrichter, parameter) for wechselrichter in globals.config.Devicenames]
        
        try:
            s=[(pp[0] + ": " + str(pp[1]) + " " + pp[2]) for pp in p]
            print (str(datetime.datetime.now()), " ".join(s), "total: " , str(p[0][1] + p[1][1]) + " " + p[0][2])
        except:
            print ('got wrong response from read_pv')
            print (p)

        time.sleep(3)

