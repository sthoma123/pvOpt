#!/usr/bin/python3

import os, glob, time, sys, datetime, re
#import cache
import config
import driverCommon
import globals

import logging
from funcLog import logged

import configparser
import struct

import archive
    
    

#----------------------------------------------------------------------------------------------------
# dump1File:
#
def dump1File(fn):

    objectClass=archive.archiveFileClass(fn, "")
    if not objectClass.open():
        print("unable to open File %s:" %  fn)
    else:
        print ("writing to file %s " % (fn + ".csv"))
        
        outFile = open(fn + ".csv", 'w')
        
        rv = objectClass.read(datetime.datetime(1970, 1, 1), 1000000)
        
        outFile.write ("File %s:\n" %  fn)
        outFile.write ("recordSize =   %d\n" % objectClass.headerRecordSize)
        outFile.write ("headerSize =   %d\n" % objectClass.headerSize)
        outFile.write ("DP         =   %s\n" % objectClass.headerDp)
        outFile.write ("dataType   =   %s\n" % objectClass.headerDataType)
        outFile.write ("unit       =   %s\n" % objectClass.headerUnit)
        outFile.write ("description=   %s\n" % objectClass.headerDesc)
        outFile.write ("timestamp; %s %s\n" % (objectClass.headerDesc, objectClass.headerUnit))
        
        if objectClass.headerDataType == "<class 'float'>":
            for d in rv:
                s="%s;  %9.5f" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), d[1])
                s=s.replace(".",",")            
                outFile.write (s+"\n")
        elif  objectClass.headerDataType == "<class 'str'>":
            for d in rv:
                s="%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), d[1])  # fuer die dlms werte!
                s=s.replace(".",",")            
                s=s.replace("'","")            
                outFile.write (s+"\n")
        else:
            for d in rv:
                outFile.write ("%s;  %s\n" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), repr(d[1])))    
    
        outFile.close()
#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main():    
  with config.configClass() as configuration:

    globals.config=configuration
    
    if len(sys.argv) < 2:
        print ("Usage: dumpArchive filename1 [filename2]...")
    else:    
        for arg in sys.argv[1:]:
            try:
                dump1File(arg)
            except Exception as e:
                print ("Exception: %s" % (repr(e)))
                
    
    return 0
    
        
    

if __name__ == "__main__":
    with config.configClass() as configuration:
        globals.gConfig= configuration
        main()
