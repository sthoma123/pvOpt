#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
print ("imported " + __name__)
#
# readConfig.py
#

import os, glob, time, sys, datetime
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged
from funcLog import timeit
import metadata

from  compileWebPage import compileWP

def flushConfig():
    return globals.config.flushConfig()

    
#----------------------------------------------------------------------------------------------------
# write:
#   stores a variable in globals.var dictionary
#   first element of dp is section
#   elements are separated by "#" because "/" could be a part of the names...
#
@logged(logging.DEBUG)
def write(dp, value, dummy=None):  #3rd parameter needed for some other writes...

    rv = metadata.read("CONFIG/" + dp, "CONFIG/" + dp)
    try:
        #print ("varWrite got %s, value %s " % (str(dp), str(value)))        
        assert type(dp) is str, "readConfig.write expects a string dp (got)" % (str(type(dp)))
        
        dpList=dp.split('#')
        section = None
        path = dp
        if len(dpList)>1:
            section=dpList[0]
            path   ="#".join(dpList[1:])
                    
        #writeConfig throws exception in case of problems
        #note that the last subkey can be something like "delete or add" in this case, the application has to ignore it in the return value.
        globals.config.writeConfig(section, {path: value}) # return exception or nothing.
        
        #remove potential delete or add:
        listOfReservedKeys=["delete", "add"]
        l=dp.split("#")  # separator hash weil das in .ini files nicht vorkommen sollte
        if l[-1] in listOfReservedKeys:
            l=l[0:-1]
            dp = "#".join(l)

        #return content of the datapoint:
        rv = read(dp)
        
    except Exception as e:
        rv [5] = "Exception"
        s ="Exception %s, %s for dp '%s'" % (type(e).__name__, str(e.args), dp)
        rv [0] = s
        logging.exception("readConfig.py")

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
    rv = list(globals.var.keys())
    return rv
    
#----------------------------------------------------------------------------------------------------
# read:
#   reads a variable from globals.var dictionary
#

@logged(logging.DEBUG)
def read(dp):
    #import web_pdb; web_pdb.set_trace() #debugging

    rv = metadata.read("CONFIG/" + dp, "CONFIG/" + dp)

    try:
        if dp is None:
            raise RuntimeError("readConfig.read got None datapoint.")
            
        
        #slash could be a part of a key, therefore the config-interface need a #
        d = globals.config.readConfig([dp])[dp]  #readConfig kann mehrere configs lesen, und gibt das ergebnis als dict zurück.
        if type(d) in [dict, str]: # warning: dict also has an iter, therefore check before iter...
            rv[1]=d
        elif hasattr(d, '__iter__'):  # hauptsächlich liste aber auch dict_keys
            rv[1]=list(d)
        else:
            raise RuntimeError("readConfig for nonexisting dp CONFIG/%s not possible" % dp)

        rv[2] = "" #str(type(rv[1])) # no type as unit.
        rv[5] = "Ok"
        
    except Exception as e:
        rv = "Exception %s, %s" % (type(e).__name__, e.args), None, "~" , datetime.datetime.now(), "CONFIG/" + dp, "Exception"
        logging.exception("readConfig.py")
            
        
    return rv
    
#----------------------------------------------------------------------------------------------------
# MAIN:
#

#-------------------------------------------------------------------------
#
#
@timeit
def main():

    logging.getLogger().setLevel(logging.DEBUG) #default for standalone usage
    ll = logging.getLevelName(logging.getLogger().level)

    with config.configClass() as configuration:
        globals.config= configuration
        
        print ("readConfig: start - with -l debug")
        
        ll = logging.getLevelName(logging.getLogger().level)
        print ("current log level is %s " %(ll))

        rv = read("zaehlerRaspi/timer#")  #sollte alles unter dem dp zurückgeben
        #rv = read("")
        print("read returned", rv)

        rv = read("zaehlerRaspi/timer")  #sollte alles unter dem dp zurückgeben
        #rv = read("")
        print("read returned", rv)
        

        if True:
            rv = write("test#subtest", "testconfig")
            print("wrteconfig-test#subtest returned", rv)
        
            rv = read("test#subtest")
            print("read config-test#subtest returned", rv)
        
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()
