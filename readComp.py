#!/usr/bin/python3
#
#  readComp.py 
#  execute any python calculation based on datapoints:
#  Usage:
#      COMP/fuehrungstext/p[0]+p[1]/("PV/PV0", "PV/PV1")
#  warning: uses eval with it's security impacts.

import os, glob, time, sys, datetime
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged

   
#----------------------------------------------------------------------------------------------------
# read:
#   DP={compWORD}
#  returns list: Name, Value, Unit, timestamp (not depending on protocol!)

@logged(logging.DEBUG)
def read(dp):

    rv = "unknown", 0, "~" , datetime.datetime.now(), "COMP/"+dp, "Unknown" 

    try:
        if dp is None:
            logging.error("readComp.read got no datapoint.")
        elif ""==dp:
            logging.error("readComp.read got empty datapoint.")

        elif type(dp) is str:
            dpList=dp.split('/')
        else:
            dpList=dp

        while len(dpList) < 3:  # brauche zumindest 2 elemente, auch wenn sie leer sind!
            dpList = dpList + [""]


        s="(" + "/".join(dpList[2:]) + ")"
        logging.debug("readComp parms evals %s" % s)
        parmDp=eval(s) # list of datapoints for parameters
        
        formula=dpList[1]

        #get values out of datapoints
        parmVal=[driverCommon.read(x) for x in  parmDp]
        p = [y[1] for y in parmVal]
        
        logging.debug("parms: p is %s" % str(p))
        
        logging.debug("readComp formula evals %s" % formula)
        
        rvVal = eval (formula) # use first value to compose return value
        logging.debug("readComp executes formula %s returns %s"  % (formula, str(rvVal)))
        
        rv = (dpList[0], rvVal, parmVal[0][2], parmVal[0][3], "COMP/" + dp, parmVal[0][5])
        
    
    except Exception as e:
        rv = "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now(), "COMP/" + dp, "Exception"
        logging.exception("readComp.py")
    
    return rv
    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
    globals.config= configuration
    
    dps=["PVTotal/p[0]+p[1]/\"PV/PV0\", \"PV/PV1\""]

    o = [read(compName) for compName in dps]
    for x in o:
        print (x)
        
    #s="x".join([str(p) for p in o])
    #print (s)
    #sys.exit()
    
    s=" ".join(
        ["\n" + pp[0] + " is " + str(pp[1]) + " " + pp[2] + ";" for pp in o]
        )
    print (str(datetime.datetime.now()),  " " , s)
    