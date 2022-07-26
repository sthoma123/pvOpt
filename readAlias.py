#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#
#  readAlias.py 
#  reads datapoints via an alias table to simplify addressing.
#  e.g. ALIAS/outTemp reads "TEMP/00042d9aabff"
#  the list of aliasses is configured in the dictionary "Alias" in config.py
#
print ("imported " + __name__)
import os, glob, time,  sys, datetime
import socket    # used for TCP/IP communication
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged
import metadata

import dpLogger
class Box:
    pass

__m = Box()  # m will contain all module-level values
__m.logBuffer = []


   
#----------------------------------------------------------------------------------------------------
# read:
#   DP={ALIASWORD}
#  returns list: Name, Value, Unit, timestamp (not depending on protocol!)

@logged(logging.DEBUG)
def read(dp):

    __m.logBuffer=[]

    rv = metadata.read("ALIAS/" + dp, "ALIAS/" + dp)    

    try:
        transDp=""
        
        if dp is None:
            logging.error("readAlias.read got no datapoint.")
        elif ""==dp:
            logging.error("readAlias.read got empty datapoint.")
        else:
            if dp not in globals.config.configMap["Alias"]:
                s="dp ALIAS/%s is not in list of Alias" % dp
                dpLogger.log(__m.logBuffer, "Error", s)
            else:
                transDp=globals.config.configMap["Alias"][dp] #throws an exception if not working
                s="readAlias.read translates %s into %s" % (dp, transDp)            
                dpLogger.log(__m.logBuffer, "readAlias", s)
                
                if "" != transDp:
                    rv=driverCommon.read(transDp)
                    rv[4]="ALIAS/"+dp
                else:
                    s="readAlias translates to  empty datapoint?"
                    dpLogger.log(__m.logBuffer, "Error", s)
                                    
    
    except Exception as e:
        s="Exception %s, %s" % (type(e).__name__, e.args)
        rv = s, 0, "~" , datetime.datetime.now(), "ALIAS/%s" %(dp), "Exception"
        dpLogger.log(__m.logBuffer, "Exception", s)
        
        logging.exception("readAlias.py")
            
    dpLogger.flushLog("ALIAS/%s" %(dp), __m.logBuffer)
    __m.logBuffer = []
        
    return rv
    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
    globals.config= configuration
    o = [read(aliasName) for aliasName in globals.config.configMap["Alias"]]
    #s="x".join([str(p) for p in o])
    #print (s)
    #sys.exit()
    
    s=" ".join(
        ["\n" + pp[0] + " is " + str(pp[1]) + ";" for pp in o]
        )
    print (str(datetime.datetime.now()),  " " , s)
    