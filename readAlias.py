#!/usr/bin/python3
#
#  readAlias.py 
#  reads datapoints via an alias table to simplify addressing.
#  e.g. ALIAS/outTemp reads "TEMP/00042d9aabff"
#  the list of aliasses is configured in the dictionary "Alias" in config.py
#

import os, glob, time,  sys, datetime
import socket    # used for TCP/IP communication
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged
   
#----------------------------------------------------------------------------------------------------
# read:
#   DP={ALIASWORD}
#  returns list: Name, Value, Unit, timestamp (not depending on protocol!)

@logged(logging.DEBUG)
def read(dp):

    rv = "unknown", 0, "~" , datetime.datetime.now(), dp, "unknown"

    try:
        transDp=""
        
        if dp is None:
            logging.error("readAlias.read got no datapoint.")
        elif ""==dp:
            logging.error("readAlias.read got empty datapoint.")
        else:
            transDp=globals.config.Alias[dp] #throws an exception if not working
            
        logging.debug("readAlias.read translates %s into %s" % (dp, transDp))
        
        if "" != transDp:
            rv=driverCommon.read(transDp)
    
    except Exception as e:
        rv = "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now(), dp, "Exception"
        logging.exception("readAlias.py")
            
        
    return rv
    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
    globals.config= configuration
    o = [read(aliasName) for aliasName in globals.config.Alias]
    #s="x".join([str(p) for p in o])
    #print (s)
    #sys.exit()
    
    s=" ".join(
        ["\n" + pp[0] + " is " + str(pp[1]) + ";" for pp in o]
        )
    print (str(datetime.datetime.now()),  " " , s)
    