#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
print ("imported " + __name__)
#"""
#
#
#.. transform transformiert datapoints, values auf Basis einer regex
#z.B. 
#  TASMOTA/devicename/POWER/1  (0)  -> MQTT/devicename/POWER1 (OFF)
#  und zurück.
# it ensures that I can write and read with the same datapoint to be able to use the normal button front-end.
# mapping from TASmota to MQTT:
#
# commands see: https://github.com/arendst/Sonoff-Tasmota/wiki/Commands
#
#   TAS/my_sonoff/power/1@broker 
#      -> write: cmnd/my_sonoff/
#      -> read /stat/my_sonoff/POWER1

#   TAS/XOR/my_sonoff/power/1@broker:
#      -> write cmnd/mySonoff/power1/TOGGLE
#      -> read cmnd/mySonoff/POWER1
#
#blink 
#
import os, glob, time, sys, datetime, queue
import helpers
import threading
import argparse
import json
import config
import globals
from funcLog import logged
import logging
import metadata
import helpers
import JSONHelper
import dpLogger

#
#----------------------------------------------------------------------------
# returns transformed value
# 3rd parameter gives root transformRule for starting regex tree (probably "rootRead" or similar)
# raises exception if transform Rule is not in config.
# transformRule cn be list or string
# returns dp, value, reverseRule(List or string)
#
def transform(dp, value, transformRules, logBuffer):

    #print("transform got dp %s, value %s, rules %s" % (dp, str(value), str(transformRules)))

    if transformRules is None:
        transformRules = []
        
    if type(transformRules) is str:
        transformRules=[transformRules]

    transformConfig = globals.config.configMap["transform"]    
    reverseRule=[]
    
    for transformRule in transformRules:
        assert transformRule is None or type(transformRule) is str, "transformRule is not str or None , got %s %s" % (str(type(transformRule)), str(transformRule))
        if transformRule != None and transformRule != "":
            if transformRule not in transformConfig:
                raise Exception("transformRule %s not in transform config" % transformRule)
                
            currRule=transformConfig[transformRule]
            assert type(currRule) is dict, "configured rule %s must be a dict , got %s %s" % (transformRule, str(type(currRule)), str(currRule))
            cnt = 1 # default handling: value will be treated
            s="TestingRule %s: %s with dp %s" %(transformRule, str(currRule), dp)
            dpLogger.log(logBuffer, "Transform", s)

            if "dp" in currRule:
                dpRule=currRule["dp"]
                assert type(dpRule) in [tuple, list], "%s.%s expect a 2-item List as dp, got %s" % (transformConfig, transformRule, str(type(dpRule)))
                assert len(dpRule) == 2, "%s.%s expect a 2-item List as dp, got %s, len %d" % (transformConfig, transformRule, str(type(dpRule), len(dpRule)))
                regDp, substDp = dpRule
                dpNew, cnt = helpers.regular(dp, regDp, substDp)
                if cnt > 0:
                    s="Rule %s changed dp %s to %s" %(transformRule, dp, dpNew)
                    dpLogger.log(logBuffer, "Transform", s)
                dp = dpNew
                
            if cnt > 0: #something matched, or no dp handling regex: also handle value:
                #reverseRule
                if "reverse" in currRule:
                    #reverseRule.append(currRule["reverse"])
                    reverseRule.insert(0, currRule["reverse"])
                if "value" in currRule:
                    valRule = currRule["value"]
                    assert type(valRule) in [tuple, list], "%s.%s expect a 2-item List as val, got %s" % (transformConfig, transformRule, str(type(valRule)))
                    assert len(valRule) == 2, "%s.%s expect a 2-item List as val, got %s, len %d" % (transformConfig, transformRule, str(valRule), len(valRule))
                    for regValRule in valRule:
                        assert len(regValRule) == 2, "%s.%s singleValRule expect a 2-item List as valRule, got %s, len %d" % (transformConfig, transformRule, str(regValRule), len(regValRule))
                        regVal, substVal = regValRule
                        # value could be anything including dict. Therefore try to convert to JSON
                        if type(value) is not str:
                            value=JSONHelper._encode(value)
                            
                        #dpLogger.log(logBuffer,"Transform", "valRule test %s to %s for data %s" %(regVal, substVal, value))
                        valueNew, dummy = helpers.regular(value, regVal, substVal)
                        if dummy > 0:
                            dpLogger.log(logBuffer,"Transform", "Rule %s changed val %s to %s" %(transformRule, value, valueNew))
                            value = valueNew
                        
            if  cnt > 0 and "nextRule" in currRule:  #nextRule only if match
                nextRules = currRule["nextRule"]                
                if  type(nextRules) is str:
                    nextRules=[nextRules]
                dp, value, r = transform(dp, value, nextRules, logBuffer)
                #reverseRule.extend(r)   
                r.extend(reverseRule)
                reverseRule=r

    #print("transform returned %s, %s, %s" % (dp, str(value), str(reverseRule)))
    return (dp, value, reverseRule)

#----------------------------------------------------------------------------------------------------
def cli():
    """Start via command line interface."""
    parser = argparse.ArgumentParser(
        description="tests transformation")
    transformRules="rootWrite"
    try:
        transformConfig = globals.config.configMap["transform"]    
        if "transformRules" in TASConfig:
            transformRules=TASConfig["transformRules"]
    except:
        pass
        
    #print ("default transform rule is %s" % transformRules)
    
    parser.add_argument("-d", "--dp", metavar='Datapoint',
                        type=str, default = "TASMOTA/MamaLampe/POWER/", 
                        help="datapoint in any form including drivername")
                        
    parser.add_argument("-v", "--value", 
                        type=str, default = "0",
                        help="value for publishing topic")

    parser.add_argument("-t", "--type", 
                        type=str, default = transformRules,
                        help="transformation rule(e.g. rootRead, rootWrite, rootEvent)")

    args = parser.parse_args()

    if all(arg in (False, None, "") for arg in (args.dp)):
        parser.print_help()
    
    return (args.dp, args.value, args.type)

    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main() :

  import driverCommon

  config.doNotParseCommandline = True  
  
  with config.configClass() as configuration:
    globals.config= configuration
    globals.shutdown = False

    dp, value, transformRules = cli() #cli needs config.
    logBuffer=[]
    
    while 1:
        if False:
            transformed = transform(dp, value, transformRules, logBuffer)
            print("transform returns %s %s %s" % transformed)
            if transformed[1]!="":
                print("Write returned %s " % str(driverCommon.write(transformed[0], transformed[1])))
            else:
                #transformed is [dp, value, next]
                print("Read returned %s " % str(driverCommon.read(transformed[0])))
                
            andBack = transform(transformed[0], transformed[1], transformed[2], logBuffer)
            print("and Back returns %s %s %s" % andBack)            
            
            globals.shutdown=True
            
            break
            
        if True:
            transformed = (dp, value, transformRules)
            if value!="":
                print("Write returned %s " % str(driverCommon.write(dp, value)))
            else:
                for i in range(1,5):
                    #transformed is [dp, value, next]
                    print("Read returned %s " % str(driverCommon.read(dp)))
                    time.sleep(2)
            break
            
    globals.shutdown = True



if __name__ == '__main__':
    config.doNotParseCommandline = True
    main()

