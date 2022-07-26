#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#
# readExec.py
#
# allowed executables are:
#  compileWebpage ()
#
print ("imported " + __name__)

import os, glob, time, sys, datetime
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged
import metadata

from  compileWebPage import compileWP

cmdList=["compileWP", "flushConfig"]

def flushConfig(dummy=None):  #currently not possible to call via webinterface without a parameter.
    return globals.config.flushConfig()

    
#----------------------------------------------------------------------------------------------------
# write:
#   stores a variable in globals.var dictionary
#
@logged(logging.DEBUG)
def write(dp, value, dummy=None):  #3rd parameter needed for some other writes...

    rv = metadata.read("EXEC/" + dp, "EXEC/" + dp)
    cmd = rv[0]
    try:
        
        #print ("varWrite got %s, value %s " % (str(dp), str(value)))
        
        if type(dp) is str:
            dpList=dp.split('/')
        else:
            dpList=dp
            
        command=dpList[0]
        if type(value) is str:
            value = value.split("/")
            
        if not (type(value) is list):
            value=[value]
        dpList.extend(value)
        
        if dpList[1] is None or dpList[1] == "None":
            parms = ""
        else:
            parms = ",".join(["'%s'"%(str(x)) for x in dpList[1:]])
            
        cmd = command + "(" + parms + ")"
        if command in cmdList:
            r=eval(cmd)
            rv[1] = r # probably convert to JSON
            rv[5]="Ok"
        else:
            raise RuntimeError('Execute %s(%s) is not possible' % (command, parms))
        
    except Exception as e:
        rv [5] = "Exception"
        s ="Exception %s, %s for command '%s'" % (type(e).__name__, str(e.args), cmd)
        rv [0] = s
        logging.exception("readExec.py")

    return rv


    #print ("varWrite step 3 rv %s, value %s " % (str(rv), str(value)))

    return rv
    
#----------------------------------------------------------------------------------------------------
# getList:
#   gets a plain list of defined variables
#   dp is a part of the datapoint (e.g. the first part of the datapoints
#
@logged(logging.DEBUG)
def getList(dp):
    rv = cmdList
    return rv
    
#----------------------------------------------------------------------------------------------------
# read:
#   reads a variable from globals.var dictionary
#

@logged(logging.DEBUG)
def read(dp):
    
    rv = metadata.read("EXEC/" + dp, "EXEC/" + dp)

    try:
        
        if dp is None:
            logging.error("readExec.read got no datapoint.")
        elif "" == dp:
            logging.error("readExec.read got empty datapoint.")
            
        raise RuntimeError("exec: read for %s currently not possible. to execute try write" % dp)
        
        rv[1] = ""
        rv[5] = "Ok"
        
    except Exception as e:
        rv = "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now(), dp, "Exception"
        logging.exception("readExec.py")
            
        
    return rv
    
#----------------------------------------------------------------------------------------------------
# MAIN:
#

#-------------------------------------------------------------------------
#
#
def main():

    logging.getLogger().setLevel(logging.DEBUG) #default for standalone usage
    ll = logging.getLevelName(logging.getLogger().level)

    with config.configClass() as configuration:
        globals.config= configuration
        
        print ("readExec: start - with -l debug")
        
        ll = logging.getLevelName(logging.getLogger().level)
        print ("current log level is %s " %(ll))

        rv = write("compileWP", "webPageDefinition")
        print("compileWebPage returned", rv)
        
        
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()
