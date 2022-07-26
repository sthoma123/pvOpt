#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#
#  metadata.py 
#  returns a tuple containg a "ZERO" or NULL value together with all the 
#  description unit and datetimestamp.
print ("imported " + __name__)
import os, glob, time, sys, datetime
import http, http.client
import json
import config
import globals
from funcLog import logged
import logging

@logged(logging.DEBUG)
def findMeta(dpList):
    rv = ""
    if type(dpList) is str:
        dpList = dpList.split("/")
        
    searchKey="/".join(dpList)
    if "METADATA" in globals.config.configMap:
        if searchKey in globals.config.configMap["METADATA"]:
            rv = globals.config.configMap["METADATA"][searchKey]
        else:
            if len(dpList) > 1:
                rv = findMeta(dpList[0:-1])
        
    return rv
    

#----------------------------------------------------------------------------------------------------
# fuellt daten mit defaultdaten aus config
#
# reads config from section METADATA
#   nameWithoutModule=Description, Unit, dataType
#   returns a list: description, value=0, unit, now, dp, status="unknown"
@logged(logging.DEBUG)
def read(dp, defaultDesc = ""):
    
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    rv = [defaultDesc, 0, "~" , datetime.datetime.now(), "/".join(dpList), "unknown"]

    meta=findMeta(dpList)
    assert type(meta) is str, "findMeta (%s) returned %s, expected str" % (str(dpList), str(type(meta)))
    
    if type(meta) is str and len(meta) > 0:
        metaList=meta.split(",")
        if len(metaList) > 0:
            rv[0]=metaList[0]   #description
        if len(metaList) > 1:
            rv[2]=metaList[1]   #Unit

    return rv
    
    
#-------------------------------------------------------------------------
#
#
if __name__ == "__main__":
    with config.configClass() as configuration:
        globals.config= configuration   
        print ("metadata: start - with - debug")
        logging.getLogger().setLevel(logging.DEBUG)
        
        rv = read ("VAR/test")
        print ("got metadata for VAR/test: ", rv)
        print ("All metadata is: ")
        for key in globals.config.configMap["METADATA"]:
            print (" %40s = %s" % (key, globals.config.configMap["METADATA"][key]))
            
        
    