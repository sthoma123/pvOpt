#!/usr/bin/python3
#
#  readVar.py 
#  reads / writes datapoints into memory. provides a persistent lastvalue.
#  e.g. Var/outTemp reads "TEMP/00042d9aabff"
#  vars are created dynamically, no need to configure
#
#  adress is VAR/anyhing/anotherthing/anythingelse
#  if configured, description, Unit etc. are taken from config. [VAR]
#
#  first parameter can have special meaning to support toggling of booleans, power calculation,
#  etc.
#  ADD, MUL, DIV, AND, OR, XOR
#

import os, glob, time, sys, datetime
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged
import metadata

#----------------------------------------------------------------------------------------------------
# write:
#   stores a variable in globals.var dictionary
#
@logged(logging.DEBUG)
def raw_write(dp, value):
    try:
        rv = metadata.read("VAR/" + dp, "VAR/" + dp)
        rv [1] = value
        globals.var[dp] = value
        rv [5] = "Ok"
        globals.gArchive.write(rv)
    except Exception as e:
        rv [5] = "Exception"
        logging.exception("readVar.py")

    return rv

#----------------------------------------------------------------------------------------------------
# 
# 
#
@logged(logging.DEBUG)
def handleOperator(a, b, operator):
    rv = 0
    if type(a) is int or type(a) is float:
        if operator == "ADD":
            rv = a + b
        elif operator == "SUB":
            rv = a - b
        elif operator == "MUL":
            rv = a - b
        elif operator == "DIV":
            rv = a - b
        else:  #here comes the bitwise operators:
            a = int(a)
            b = int(b)
            if operator == "XOR":
                rv = a ^ b        
            elif operator == "OR":
                rv = a | b        
            elif operator == "AND":
                rv = a & b
    
    return rv
    
#----------------------------------------------------------------------------------------------------
# write:
#   stores a variable in globals.var dictionary
#
@logged(logging.DEBUG)
def write(dp, value, dummy=None):  #3rd parameter needed for some other writes...

    rv = list()
    
    #print ("varWrite got %s, value %s " % (str(dp), str(value)))
    
    cmdList=["ADD", "SUB", "XOR", "OR", "AND", "MUL", "DIV"]
    operator = "SET"
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp
        
    if dpList[0] in cmdList:
        operator=dpList[0]
        dpList=dpList[1:]
    
    dp="/".join(dpList)

    #    print ("varWrite step 2 %s, value %s " % (str(dp), str(value)))
    
    if operator in cmdList:
        rv = read(dp)
        value = handleOperator(rv[1], value, operator)
    
    rv =  raw_write(dp, value)

    #print ("varWrite step 3 rv %s, value %s " % (str(rv), str(value)))

    return rv
    
#----------------------------------------------------------------------------------------------------
# getList:
#   gets a plain list of defined variables
#   dp is a part of the datapoint (e.g. the first part of the datapoints
#
@logged(logging.DEBUG)
def getList(dp):
    rv = globals.var.keys()
    return rv
    
#----------------------------------------------------------------------------------------------------
# read:
#   reads a variable from globals.var dictionary
#

@logged(logging.DEBUG)
def read(dp):
    
    rv = metadata.read("VAR/" + dp, "VAR/" + dp)

    try:
        
        if dp is None:
            logging.error("readVar.read got no datapoint.")
        elif "" == dp:
            logging.error("readVar.read got empty datapoint.")
            
        if dp not in globals.var:
            # lese letztwert aus Archiv:
            ar = globals.gArchive.read("VAR/"+dp, datetime.datetime.now(), -1)
            print ("var.read gets from archive: ", ar)
            if len(ar) > 0:
                globals.var[dp]=ar[0][1]
            else:
                globals.var[dp]=None
            
        rv[1] = globals.var[dp]
        rv[5] = "Ok"
        
    except Exception as e:
        rv = "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now(), dp, "Exception"
        logging.exception("readVar.py")
            
        
    return rv
    
#----------------------------------------------------------------------------------------------------
# MAIN:
#

#-------------------------------------------------------------------------
#
#
def main():

    with config.configClass() as configuration:
        globals.config= configuration   
        print ("metadata: start - with - debug")
        logging.getLogger().setLevel(logging.DEBUG)
        rv = read ("ZAEHLERBILANZ")
        print ("got variable for VAR/ZAEHLERBILANZ: ", rv)

        rv = write ("ZAEHLERBILANZ", 1)
        
        
        rv = read ("test")
        print ("got variable for VAR/test: ", rv)
        
        rv = write("test2", 42)
        
        rv = getList("")
        print ("Got list of variables: ", rv)
        
        print ("All variables defined are: ")
        for key in globals.var:
            print ("key %40s = %s" % (key, str(globals.var[key])))
            
        
        
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()
