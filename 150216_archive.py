#!/usr/bin/python3

import os, glob, time, gspread, sys, datetime
import globals
#import cache
import config
from funcLog import logged
import logging
import configparser
import struct

#----------------------------------------------------------------------------------------------------
# this is the backend class for the archive access:
# it should be used by the archive server to be able to serve requests from memory
# and to write files blockwise (cache)
# interface:
#    readinfo(dp) # returns name, unit, timestamp-from / to, n
#
#    read(dp, timestampFrom, timestampTo = 0, n=1) # reads number of values since timestamp (if timestamp is not exact, timestamp before is returned)
#           # returns list datalist:(value,  timestamp)
#
#    write(dp, name, unit, datalist:(value,  timestamp))
#
# structure and helper functions archivefilebased:
# archiveFileClass:
#
#
#   private filenameprefix(dp) 
#       -> returns name of file (no special characters, path from pvOpt.ini)
#   private archiveFile.open (dp, timestamp) 
#       -> opens file containing data to that dp/timestamp, reads header
#
#   public archiveFile.write(name, unit, datalist:(value,  timestamp))
#       -> creates the file and writes the Header
#   
#   public archiveFile.read (n)
#   public archiveFile.readNext(n)
#
#(name, unit, datalist:(value,  timestamp))
#       -> creates the file and writes the Header
#   
#----------------------------------------------------------
# fileformat
# fileformat: fix - datapoint-start-timestamp(first sample)
#
# fileformat pvArchiv
# 1: (int) recordlänge
# 2: Haederlaenge
# 3: header:
# 3.a Datapoint (fullname)
# 3.b datatype
# 3.c unit
# 3.d Granularity time (in secs (e.g. once every day)
# 3.e Granularity value (absolut ) every day 23:55
# 3.f scheduler options
# start-of-data [timestamp, value] fixed length
#       
#

#----------------------------------------------------------------------------------------------------
# archiveDP klasse entspricht einem datenpunkt, stellt auf datenpunktebene
# zugriffsfunktionen für das Archiv zur Verfügung.
#
class archiveDP:

    def __init__(self, dp):
        self.__dp=dp

    @logged(logging.DEBUG)
    def read(self, timestamp):
        return None
    
    @logged(logging.DEBUG)
    def close(self):
        return None

    @logged(logging.DEBUG)
    def flush(self):
        return None

        
#----------------------------------------------------------------------------------------------------
# archiveFile klasse entspricht einem datenpunktfile, stellt auf datenfileebene
# zugriffsfunktionen für das Archiv zur Verfügung.
#
class archiveFile:
    def __init__(self, filename):
        self.__file=None
        self.__filename = filename

    @logged(logging.DEBUG)
    def read(self, timestamp, n):
        return None

    @logged(logging.DEBUG)
    def close(self):
        return None

    @logged(logging.DEBUG)
    def flush(self):
        return None
        
    
    
#----------------------------------------------------------------------------------------------------
# ist der container für die archive DP klasse, verwaltet Liste von archiveDP
#
class archive:
    def __init__(self):        
        pass

#closes all open archiveDP (and files)
    def close(self):
        pass

#flushes all open archiveDP (and files)
    def flush(self):
        pass

    #----------------------------------------------------------------------------------------------------
    # read 
    #
    @logged(logging.DEBUG)
    def readArchive(dp, timestamp, n):
        pass

    #----------------------------------------------------------------------------------------------------
    # write
    # 
    @logged(logging.DEBUG)
    def writeArchive(dp):

        rv = None
        return rv

        
        

IFMT = ">I"
FFMT = ">d"


#----------------------------------------------------------------------------------------------------
# Buffer conversion helper functions:
#
#
def timeToBuf(t):
    f=time.mktime(t.timetuple())
    return (floatToBuf(f))
        
def bufToTime(buf):
    f=bufToFloat(buf)
    return datetime.datetime.fromtimestamp(f)

def stringToBuf(s):
    b=s.encode("utf-8")
    i=len(b)
    buf= struct.pack(">I", i) + b
    return buf


def bufToString(buf):
    len=struct.unpack(IFMT, buf[0:4])[0]
    a=struct.calcsize(IFMT)
    b=a+len
    try:
        s=buf[a:b].decode("utf-8")    
    except:
        logging.exception("unable to decode string from buf, len %d" % len)
        s="???"        
    return s

def floatToBuf(f):
    return struct.pack(FFMT,f)

def bufToFloat(buf):
    return struct.unpack(FFMT, buf)[0]

def intToBuf(i):
    return struct.pack(IFMT,i)
    
def bufToInt(buf):
    return struct.unpack(IFMT, buf)[0]
    
#----------------------------------------------------------------------------------------------------
# readString:
#
LENOFINT=4
def readString(file):
    len=struct.unpack(">I", file.read(LENOFINT))[0]
    s=file.read(len).decode("utf-8")    
    return s

#----------------------------------------------------------------------------------------------------
# writeString:
#
@logged(logging.DEBUG)
def writeString(file, s):
    b=s.encode("utf-8")
    i=len(b)
    file.write(struct.pack(">I", i))
    file.write(b)

        
#----------------------------------------------------------------------------------------------------
# readHeader:
#
@logged(logging.DEBUG)
def readHeader(file):
    #returns tuple (recordSize, headerSize, datapoint, datatype, unit)
    try:
        recordSize =struct.unpack(">I",file.read(LENOFINT))[0] # one integer
        headerSize =struct.unpack(">I",file.read(LENOFINT))[0] # one integer
        datapoint  =readString(file) # one string with len/ascii
        datatype  =readString(file) # one string with len/ascii
        unit  =readString(file) # one string with len/ascii
        rv=(recordSize, headerSize, datapoint, datatype, unit)
        
    except:
        rv=(None, None, None, None, None)

    return rv
    
#----------------------------------------------------------------------------------------------------
# getFileName:
#    returns name according to datapoint (without datetime-postfix)
#
@logged(logging.DEBUG)
def getFileName(datapoint):
    #substitute everything that could disturb a filename 
    nonChars =".,;:<>|/\\!§$%&/()=\"^°+*#\'"
    rv = datapoint.lower()
    for ch in nonChars:
        rv = rv.replace(ch, "_")
    # and append basic path:
    
    rv = globals.gConfig.archivepath + rv  
    
    return rv
    
#----------------------------------------------------------------------------------------------------
# getArchiveFileName:
#    returns existing or new file from datapoint and timestamp
#    searches for file on or before the given timestamp 
#    returns file with timestamp given if nonexisting or file exceeds maxSize from configuration
#
@logged(logging.DEBUG)
def getArchiveFileName(datapoint, timestamp):
    #schau mer mal ob schon eins da ist:
    fn = getFileName(datapoint)
    searchName = fn + "-2???-??-??_??.??.??*" + globals.gConfig.archiveext
    fileNames = sorted(glob.glob(searchName))
    
    # = [s.split('-')[1] for s in glob.glob(searchName)]
    print ("Available filenames: ", fileNames)
    
    rv = list()
    
    #return youngest and new one (don't know if youngest header fits!)
    if len (fileNames) > 0:
        rv.append(fileNames[-1])
    else:
        rv.append(None)
       
    rv.append(fn + "-" + timestamp.strftime("%Y-%m-%d_%H.%M.%S") + globals.gConfig.archiveext)
    
    return rv

    
#----------------------------------------------------------------------------------------------------
# checkHeader:
#    checks if header is fine. returns false if not
@logged(logging.DEBUG)
def checkHeader(file, recordSize, headerSize, datapoint, datatype, unit):

    rv=True
    h=readHeader(file)
    
    if h[0] is not None and recordSize != h[0]:
        logging.error('opening file %s: header mismatch: recordsize %d instead of %d' % (filename, h[0], recordSize))        
        rv = False
        
    if h[1] is not None and headerSize != h[1]:
        logging.error('opening file %s: header mismatch: headerSize %d instead of %d' % (filename, h[1], headerSize))        
        rv = False

    if h[2] is not None and datapoint != h[2]:
        logging.error('opening file %s: header mismatch: datapoint %s instead of %s' % (filename, h[2], datapoint))        
        rv = False

    if h[3] is not None and datatype != h[3]:
        logging.error('opening file %s: header mismatch: datatype %s instead of %s' % (filename, h[3], datatype))        
        rv = False

    if h[4] is not None and unit != h[4]:
        logging.error('opening file %s: header mismatch: unit %s instead of %s' % (filename, h[4], unit))        
        rv = False

    return rv
    
#----------------------------------------------------------------------------------------------------
# writeHeader:
#    returns open file handler ready for writing 
#    if everything is fine (either existing header is Ok or header is written)
#
@logged(logging.DEBUG)
def openCheckFile(filename, recordSize, headerSize, datapoint, datatype, unit):

    rv = None
    file = None
    err=False
    
    if filename[0] is not None:
        try:
            file=open(filename[0] , 'rb+')
            # header has to match, otherwise i have to create another file
            if not checkHeader(file, recordSize, headerSize, datapoint, datatype, unit):
                file.close()
                file=None
        except IOError as e:
            #not necessarily an error since file just does not exist...
            file=None
            pass
        
    try:
        if file is None:  #try other file (new one)
            file=open(filename[1], 'wb+')
            file.write(struct.pack(">I", recordSize))
            file.write(struct.pack(">I", headerSize)) # one integer
            writeString(file, datapoint) 
            writeString(file, datatype) 
            writeString(file, unit) 
            
            logging.info("archive created file %s" % filename[1])
        
    except IOError as e:
        logging.exception("unable to write header to file %s " % filename)
        err=True        
            
    if err and (file is not None):
        file.close()
        file = None

    if file is not None:
        file.seek(0, 2)  #to the End!.
        
    return file
    
#----------------------------------------------------------------------------------------------------
# readArchive:
#       reads n values from the archive (within a file)
#       try a binary search
#
def readArchive(file, timestamp, n):
    return None


#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
    gConfig=configuration
    
    print (globals.config)
    
    headerSize=55
    datapoint="PV/PV0/testdatapoint"

    filename = getArchiveFileName(datapoint, datetime.datetime.now())
    
    print ("got filename " + str(filename))
    datatype="datatypesdfismyownone"
    unit="kWh"
    
    dataToWrite=timeToBuf(datetime.datetime.now()) + stringToBuf("Thisisdata")
    recordSize=len(dataToWrite)
    
    file = openCheckFile(filename, recordSize, headerSize, datapoint, datatype, unit)
    if file is not None:
        for number in range(1,101): 
            file.write(dataToWrite)
        print ("wrote to file %s " % file.name)
        file.close()
        file=None
        
        #dataRead = readArchive(file, n)
        
        
        
    

