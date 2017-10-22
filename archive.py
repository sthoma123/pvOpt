#!/usr/bin/python3


#todo:
# max, min avg, 
# einschaltdauer prozentuell(?) alternativ summenhäufigkeit
# memory datenpunkte aufsummieren.
#

import os, glob, time, sys, datetime, re
#import cache
import config
import driverCommon
import globals

import logging
from funcLog import logged
#für sort:
from operator import itemgetter

##import configparser
import struct

#----------------------------------------------------------------------------------------------------
HEADERERROR = 47120815  #just a significant random number
LENOFBOOL=1
LENOFINT=4
LENOFTIME=8
LENOFFLOAT=8
IFMT = ">I"
BFMT = ">?"
FFMT = ">d"


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
#   private archiveFileClass.open (dp, timestamp) 
#       -> opens file containing data to that dp/timestamp, reads header
#
#   public archiveFileClass.write(name, unit, datalist:(value,  timestamp))
#       -> creates the file and writes the Header
#   
#   public archiveFileClass.read (n)
#   public archiveFileClass.readNext(n)
#
#(name, unit, datalist:(value,  timestamp))
#       -> creates the file and writes the Header
#   
#----------------------------------------------------------
# fileformat
# fileformat: fix - dp-start-timestamp(first sample)
#
# fileformat pvArchiv
# 1: (int) recordlaenge
# 2: Haederlaenge
# 3: header:
# 3.a dp (fullname)
# 3.b datatype
# 3.c unit
# 3.d Granularity time (in secs (e.g. once every day)
# 3.e Granularity value (absolut ) every day 23:55
# 3.f scheduler options
# start-of-data [timestamp, value] fixed length
#       
#

#----------------------------------------------------------------------------------------------------
#
#  archiveDPClass::timestampFromFilename(fn)
#returns timestamp
@logged(logging.DEBUG)
def timestampFromFilename(fn):
    rv = None
    try:
        s=re.findall(r'\d{4}-\d{2}-\d{2}_\d{2}.\d{2}.\d{2}', fn)[0]
        t=datetime.datetime(
            int(s[0:4]), int(s[5:7]), int(s[8:10]),
            int(s[11:13]), int(s[14:16]), int(s[17:19]))
            
        #print ("timestamp is ", repr (t))
        rv = t

    except:
        logging.exception ("Unable to get timestamp from filename %s " % fn)
        
    return rv

    

#----------------------------------------------------------------------------------------------------
# archiveFileClass klasse entspricht einem datenpunktfile, stellt auf datenfileebene
# zugriffsfunktionen für das Archiv zur Verfügung.
#
class archiveFileClass:
    def __init__(self, filename, dp):
        self.file=None
        self.filename = filename
        self.recordSize = 0
        self.headerSize = 0
        self.dp = dp
        self.datatype = ""
        self.unit=""
        self.headerDp = ""
        self.headerDataType=""
        self.headerUnit=""
        self.headerDesc=""
        self.headerRecordSize=0
        self.timestamp=timestampFromFilename(filename)
        self.lastData=[self.timestamp, -99.9]  #default for empty file.
        self.fileSize=0
        
        co=globals.gConfig.__dict__
        self.compress = 0.0
        self.timeCompress = ""
        
        if self.dp in co:
            if "compress" in co[self.dp]:
                self.compress=float(co[self.dp]["compress"])
            if "timeCompress" in co[self.dp]:
                self.timeCompress=co[self.dp]["timeCompress"]   #strftime string for significance.

    def __repr__ (self):
        s="Object  archiveFileClass for file %s" % (self.filename)
        return s
        
    #----------------------------------------------------------------------------------------------------
    #  file::read1()
    # reads 1 data from the current position in the file. (returns tiemstamp/value tuple)
    #
    #
    @logged(logging.DEBUG)
    def read1(self):
    
        #pos=self.file.tell()
        #pos = 0
    
        rv=list()

        b=self.file.read(self.headerRecordSize)
        if len(b) < self.headerRecordSize:
            rv = None
        else:
            #print ("after read: filepos %d of %d" % (self.file.tell(), self.fileSize))
            
            t=b[0:LENOFTIME]
            if len(t) == LENOFTIME:                
                tt=bufToTime(t)     #manchmal kommt 1.1.1970 rein, da muss ich auf nix mappen.
                if tt == None:
                    rv = None
                else:
                    rv.append(tt)

                    #d=self.file.read(self.headerRecordSize - LENOFTIME)
                    d=b[LENOFTIME:]
                    if len(d) > 0:
                        if self.headerDataType == "<class 'float'>":
                            rv.append(bufToFloat(d))
                        elif self.headerDataType == "<class 'str'>":
                            rv.append(bufToString(d))
                        elif self.headerDataType == "<class 'int'>":
                            rv.append(bufToInt(d))
                        elif self.headerDataType == "<class 'bool'>":
                            rv.append(bufToBool(d))
                        else:
                            rv.append( None)
            
        #if len(rv)> 0:
        #    logging.debug("archiveFileClass::read1 at pos %4d returned %s, %s" % (pos, rv[0].strftime("%Y/%m/%d %H:%M:%S"), repr(rv[1])))
        
        return rv
    
    #----------------------------------------------------------------------------------------------------
    #
    #
    def __repr__ (self):
        s=""
        if (self.headerRecordSize != 0 and self.timestamp is not None and self.lastData is not None):
            if (type(self.timestamp) == datetime.datetime and 
            type(self.lastData[0]) == datetime.datetime):
                s=  "class archiveFileClass: %s size %d, containing %d records from %s to %s" % (self.filename, 
                    self.fileSize,
                    (self.fileSize - self.headerSize) / self.headerRecordSize,
                    self.timestamp.strftime("%Y/%m/%d %H:%M:%S"),
                    self.lastData[0].strftime("%Y/%m/%d %H:%M:%S"))
            
        return s
  
        
    #----------------------------------------------------------------------------------------------------
    # open öffnet oder legt ein neues File an:
    #
    @logged(logging.DEBUG)
    def open(self):
    
        rv = True
        
        if self.file is not None:
            try:  # just a try to close it
                self.file.close()
                self.file=None
            except:
                pass
            
        try:
            if len(globals.listOfOpenFiles) > 100: #close older files
                for f in globals.listOfOpenFiles[0:10]:
                    if not f.file is None:
                        #print ("number of Open file too big, closing %s " % f.filename)
                        f.close()
                globals.listOfOpenFiles=globals.listOfOpenFiles[10:]        

            self.file=open(self.filename , 'rb+')
            globals.listOfOpenFiles.append(self)
            self.readHeader()
                            
        except IOError as e:
            #not necessarily an error since file just does not exist...
            # create empty file for writing:            
            rv = False
            self.file=None
            pass

        try:            

            if self.file is None:
                self.file=open(self.filename, 'wb+')
                self.headerSize=0 # to indicate that a header has to be written (can be done when writing!
                logging.info("archive created file %s" % self.filename)
                
            self.file.seek(0,2)
            self.fileSize = self.file.tell()

                
            if self.headerSize > 0 and self.headerRecordSize > 0 and self.fileSize > self.headerRecordSize:
                # read lastvalues and timestamp
                self.file.seek((-1)*self.headerRecordSize,2)
                if self.file.tell() >= self.headerSize:
                    self.lastData = self.read1()
                    
        except IOError as e:
            logging.exception("unable to open %s for writing" % self.filename)
        
        return rv

    #----------------------------------------------------------------------------------------------------
    #
    # archiveFileClass::binSeek:
    #   positioniert auf die Seite des zieltimetamps
    #   wird hier rekursiv verwendet
    #   lbound, ubound are bytepositions
    #
    @logged(logging.DEBUG)
    def binSeek(self, lBound, uBound, timestamp):
        
        jumpTo = lBound + self.headerRecordSize * int((uBound - lBound) / self.headerRecordSize / 2)
        #mitte zwischen ubound und lbound

        self.file.seek(jumpTo, 0) # da das read aus der letzten iteration den nächsten anzeigt.

        if jumpTo == lBound or jumpTo == uBound: #nichts mehr zu holen!
            #print ("binseek fertig, nix mehr zu holen: jumpto %d, lBound %d, uBound %d" %(jumpTo, lBound, uBound))
            return None   # found!!

        #print ("binSeek Jumps to ", jumpTo)
        
        x=self.read1()
        if not x is None:            
            #s="binseek " + str(x[0]) + " >= " + str(timestamp)
            if x[0] == timestamp:
                #print (s + " equal, found exactly!!!")
                #print ("binseek fertig, EXAKT: jumpto %d, lBound %d, uBound %d" %(jumpTo, lBound, uBound))
                self.file.seek(jumpTo, 0) # found exactly
                return None        
            elif x[0] > timestamp:
                #print (s + " true")
                return self.binSeek(lBound, jumpTo, timestamp)
            else:
                #print (s + " false")
                return self.binSeek(jumpTo, uBound, timestamp)
                
        #print("binSeek none path, sollte nicht auftreten!")
        return None
    
    #----------------------------------------------------------------------------------------------------
    #
    # archiveFileClass::seekTimestamp:
    #   positioniert zum ersten eintrag der vor dem gegebenen timestamp ist (ich kann nicht erwarten die genaue Zeit zu treffen)
    #
    @logged(logging.DEBUG)
    def seekTimestamp(self, timestamp):
        rv = True
        # ich nehme an, dass die timestamps gleichverteilt ist. d.h. ich positioniere mich prozentuell 
        # dorthin wo ich glaube zu sein
        self.file.seek(0, 2)
        filesize=self.file.tell()
        self.file.seek(self.headerSize, 0)  # if there is just 1 entry, position after the header!        
        # ubound muss hinter den letzten zeigen, daher muss ich die recordsize nicht abziehen von der filesize
        # sonst wird der letzte record nie gefunden! (- self.headerRecordSize)
        x = self.binSeek(self.headerSize, filesize , timestamp)
        
        #print("seekTimestamp search %s return  %s from: %d, to %d, returned pos %d" % (timestamp, x, self.headerSize, filesize - self.headerRecordSize, self.file.tell()))        
        #print ("seekTimeStamp position returned %d ", self.file.tell())
        
        #percentage = (timestamp - self.timestamp) / (self.lastdata[0] - self.timestamp)
        
        return rv
    
    #----------------------------------------------------------------------------------------------------
    #
    # archiveFileClass::read:
    #
    #
    #
    @logged(logging.DEBUG)
    def read(self, timestamp, n, timeDelta = None):
    
        direction=int(n/abs(n))
        rv = list()
        
        if self.file is None:  #open or create:
            self.open()
            
        if self.headerSize != 0:   # file probably empty...
            self.seekTimestamp(timestamp)        
            while abs(n) > 0:
                #print ("fileClass::read: try at position %d " % self.file.tell())
                dat=self.read1()
                
                if dat is  None:   # maybe EOF
                    #print ("fileClass::read: am at the end ??: break")
                    break     
                    
                if len(dat) > 0:
                    rv.append(dat)
                    
                n = n-direction
                if direction < 0:
                    try:
                        self.file.seek(self.headerRecordSize*(-2), 1)  #relative positionierung.
                    except:
                        break    # da is nix in dem file, Abmarsch!
                    if self.file.tell() < self.headerSize:
                        #print ("fileClass::read: am at beginnig: break")
                        break
                        
        #print ("fileClass::read: returned %s " % (str(rv)))

        return rv

   #----------------------------------------------------------------------------------------------------
    # writeHeader:
    #    returns open file handler ready for writing 
    #    if everything is fine (either existing header is Ok or header is written)
    #
    @logged(logging.DEBUG)
    def writeHeader(self, recordSize, dataType, unit, desc):
    
        rv = False
        
        try:
            self.file.seek(0,0)            
            headerBuf=list()
            headerBuf.append(struct.pack(">I", recordSize))
            headerBuf.append(struct.pack(">I", 0))  #platzhalter für headersize
            headerBuf.append(stringToBuf(self.dp))
            headerBuf.append(stringToBuf(dataType))
            headerBuf.append(stringToBuf(unit))
            headerBuf.append(stringToBuf(desc))
            headerSize=0
            for b in headerBuf:
                headerSize = headerSize + len(b)

            headerBuf[1]=struct.pack(">I", headerSize)
            for b in headerBuf:
                self.file.write(b)
            
            self.headerRecordSize = recordSize
            self.headerSize = headerSize
            self.headerDp=self.dp
            self.headerDataType = dataType
            self.headerUnit = unit
            self.headerDesc = desc
            
            rv = True
        except IOError as e:
            logging.exception("unable to write header to file %s " % self.filename)
            err=True        
            
        return rv


    #----------------------------------------------------------------------------------------------------
    # compareCompress returns true if value has changed more than compress
    # problem with strings,
    # should work for int/float/boolean
    # 
    @logged(logging.DEBUG)
    def compareCompress(self, lastvalue, newvalue, timeStampTo, timestamp):
        #logging.error("compareCompress: for %s" %(self.dp))

        rv = False

        if type(newvalue) == str:
            rv = True
            if self.compress != 0:  
                if lastvalue == newvalue:
                    rv = False
        else:
            #logging.error("compareCompress: self.compress is %s value %s, %s" %(str(self.compress), str(lastvalue), str(newvalue)))
            
            try:
                if lastvalue == None or self.compress == 0:
                    rv = True
                    
                if newvalue == None:
                    rv = False
                elif rv == False:
                    diff=abs(float(lastvalue) - float(newvalue))
                    if diff >= self.compress:
                        rv=True
                 
            except:
                logging.exception("problem while calculating compression")
                rv=True

        if rv:  #timecompress could be against writing:
            try:
                if self.timeCompress is not None and len(self.timeCompress) > 0:
                
                    lasttimstr=timeStampTo.strftime(self.timeCompress)
                    newtimstr=timestamp.strftime(self.timeCompress)
                    #logging.error("compareCompress: timeCompress2 %s, %s" %(lasttimstr, newtimstr))
                    
                    #print ("Archive 397: lasttimstr, newtimstr ", newtimstr, lasttimstr)
                    
                    #print ("compreCompress - 3 lasttimstr=%s, newtimstr=%s"% (lasttimstr, newtimstr))
                    if lasttimstr == newtimstr:
                        rv = False
            except:
                logging.exception("unable to time-compress with strftime %s" % self.timeCompress)

        #logging.error("compareCompress: returns %s" %(rv))
                
        return rv
    #----------------------------------------------------------------------------------------------------
    #
    #  archiveFileClass::getInfo()
    #    returns a tuple of information:
    #       desc, unit, timestampfrom-to, dataType, NumberOfEntries, 
    #
    @logged(logging.DEBUG)
    def getInfo(self):

        rv= [ "", "", None, None, None, 0, self.dp]
        # open files:
    
        if self.file is None:  #open or create:
            self.open()
        if not self.file is None:
            rv [0] = self.headerDesc
            rv [1] = self.headerUnit
            rv [2] = self.timestamp
            if self.lastData != None:
                rv [3] = self.lastData[0]
            
            rv [4] = self.headerDataType
            if self.headerRecordSize > 0:
                #print ("filesize, headersize, headerRecordSize", filesize, headersize, headerRecordSize)
                rv [5] = int((self.fileSize - self.headerSize) / self.headerRecordSize)
                
            rv [6] = self.headerDp
            
        #rv[0]="nixi"
            
        return rv
                
        
    #----------------------------------------------------------------------------------------------------
    #  archiveFileClass::write()
    # returns 
    #   HEADERERROR if there is a problem with the header
    #   1   if there is another problem
    #   0   on success
    #
    
    @logged(logging.DEBUG)
    def write(self, desc, value, unit, timestamp):

        rv = 0

        if self.file is None:  #open or create:
            self.open()
            
        if timestamp is None:  # default is now:
            timestamp = datetime.datetime.now()
            
        if self.lastData is None: # habe offenbar noch nix just to be sure:
            self.lastData=[self.timestamp, -99.9]  #default for empty file.
        
        # sometimes, values come twice: direct and via alias: skip everything with same timestamp:
        if timestamp != self.lastData[0]:
            #check if value also to be compressed (ignored)
            # headersize zero is a new file!
            if (self.headerSize == 0 or 
                self.compareCompress(self.lastData[1], value, self.lastData[0], timestamp)):  # ok to write:
                
                self.lastData[0]=timestamp
                self.lastData[1]=value
            
                dataToWrite=timeToBuf(timestamp) + xToBuf(value)
                recordSize = len(dataToWrite)
                dataType=repr(type(value))
                
                #print ("write: datatype is %s "% dataType)
                    
                if self.headerSize == 0:  # new file, no data upto now.
                    # empty file, has to write header:
                    self.writeHeader(recordSize, dataType, unit, desc)
                    self.fileSize += self.headerSize
                    
                if self.file is not None: # everything fine up to now:
                    rv = self.checkHeader(recordSize, dataType, unit, desc)
                    
                if 0==rv:
                    try:
                        self.file.seek(0,2)
                        self.file.write(dataToWrite)
                        rest = self.headerRecordSize - len(dataToWrite)
                        if rest>0:
                            self.file.write (b'x'*rest)  #tuple repetition in bytes...
                            #logging.error("archive.write had to fill record with %d bytes" % rest)
                        
                        self.fileSize += self.recordSize
                    except IOError as e:
                        rv = 1
                        logging.exception("unable to write to file %s" % self.filename)
        
        return rv

    #----------------------------------------------------------------------------------------------------
    @logged(logging.DEBUG)
    def close(self):
        
        if self.file is not None:
            #self.flush()  # to be sure if there is cached data!
            self.file.close()
            self.file=None
            logging.debug("File %s closed" % self.filename)
            
        return None

    #----------------------------------------------------------------------------------------------------
    @logged(logging.DEBUG)
    def flush(self):
    
        if self.file is not None:
            self.file.flush()
        
        return None
        
    #----------------------------------------------------------------------------------------------------
    # archiveFileClass::readHeader:
    #
    @logged(logging.DEBUG)
    def readHeader(self):
        rv = False
        
        if self.file is not None:
            self.file.seek(0, 0)  #to the beginning!.

            try:
                s = self.file.read(LENOFINT)
                if (len(s) == LENOFINT):
                    self.headerRecordSize =struct.unpack(">I",s)[0] # one integer
                    
                s = self.file.read(LENOFINT)
                if (len(s) == LENOFINT):
                    self.headerSize =struct.unpack(">I",s)[0] # one integer
                
                if self.file.tell() < self.headerSize:
                    self.headerDp =readString(self.file) # one string with len/ascii
                    self.dp=self.headerDp
                    
                if self.file.tell() < self.headerSize:
                    self.headerDataType   =readString(self.file) # one string with len/ascii

                if self.file.tell() < self.headerSize:
                    self.headerUnit       =readString(self.file) # one string with len/ascii
                    
                if self.file.tell() < self.headerSize:
                    self.headerDesc       =readString(self.file) # one string with len/ascii
                    
                rv = True
                
            except:
                # probably empty file
                self.headersize=0  # to indicate, there is no valid header.
                logging.exception("unable to read Header for file: %s" %(self.filename))
                
                pass
                        
        
        return rv
    
    #----------------------------------------------------------------------------------------------------
    # checkHeader:
    #    checks if header is fine. returns false if not
    @logged(logging.DEBUG)
    def checkHeader(self, recordSize,  datatype, unit, desc): # headersize check ich nicht, da ich den header dafür zusammenbauen muesste...

        rv=0
        
        if recordSize > self.headerRecordSize:  # wenn record kleiner ist, ist kein problem, wird aufgefüllt (für stringtypen)
            logging.error('opening file %s: header mismatch: recordsize %d instead of %d' % (self.filename, self.headerRecordSize, recordSize))        
            rv = HEADERERROR
                    
        if self.dp != self.headerDp:
            logging.error('opening file %s: header mismatch: dp %s instead of %s' % (self.filename, self.headerDp, self.dp ))        
            rv = HEADERERROR

        if datatype != self.headerDataType:
            logging.error('opening file %s: header mismatch: datatype %s instead of %s' % (self.filename, self.headerDataType, datatype))        
            rv = HEADERERROR

        # in der unit gebe ich den retry counter an...
        #if unit != self.headerUnit:
        #    logging.error('opening file %s: header mismatch: unit %s instead of %s' % (self.filename, self.headerUnit, unit))        
        #    rv = HEADERERROR

        if desc != self.headerDesc:
            logging.error('opening file %s: header mismatch: Desc %s instead of %s' % (self.filename, self.headerDesc, desc))        
            rv = HEADERERROR

        return rv
        
        
#----------------------------------------------------------------------------------------------------
# archiveDPClass klasse entspricht einem datenpunkt, stellt auf datenpunktebene
# zugriffsfunktionen für das Archiv zur Verfügung.
#
class archiveDPClass:

    def __init__(self, dp):
        self.dp=dp
        # leg mal gleich alle files als archiveFileClass an die ich finde:
        self.fileList = list()

    def __repr__ (self):
        s="Object archiveDPClass for dp %s" % (self.dp)
        return s
    
    @logged(logging.DEBUG)
    def close(self):
        for x in self.fileList:
            x.flush()
            x.close()                
        self.fileList = list()
        self.timestamps=list()
        return None

    @logged(logging.DEBUG)
    def flush(self):
        for x in self.fileList:
            x.flush()
        return None

        
    #-------------------------------------------------------------------------------------------------
    # returns a new filename for the given dp and timestamp
    #
    def getNewFilename(self, tim):
        fn = getFileName(self.dp)
        rv = fn + "-" + tim.strftime("%Y-%m-%d_%H.%M.%S") + globals.gConfig.archiveext
        return rv
    
    #-------------------------------------------------------------------------------------------------
    # returns list of archiveFileClass objects()
    #
    @logged(logging.DEBUG)
    def getFileList(self, tim):
        rv = list()
        
        fn = getFileName(self.dp)
        #fn = fn.replace('[', 'x[x')
        #fn = fn.replace(']', 'x]x')
        #fn = fn.replace('x[x', '[[]')
        #fn = fn.replace('x]x', '[]]')
        #fn = fn.replace(' ', '[ ]')
        fn = escape_glob(fn)
        searchName = fn + "-2???-??-??_??.??.??*" + globals.gConfig.archiveext
        fileNames = sorted(glob.glob(searchName))        
        
        # = [s.split('-')[1] for s in glob.glob(searchName)]
        if len(fileNames) > 0:
            rv = [archiveFileClass(fi, self.dp) for fi in fileNames]
        else: # give the next one to be created (handled within archiveFile)
            if tim is not None:
                fi = self.getNewFilename(tim)
                rv = [archiveFileClass(fi, self.dp), ]
        
        return rv
        
    #----------------------------------------------------------------------------------------------------
    # 
    # archiveDPClass::read()
    #
    @logged(logging.DEBUG)
    def read(self, timestamp, n):
    
    
        rv = list()
        direction=int(n/abs(n))
        
        # check which file to use:
        if len (self.fileList) == 0:
            self.fileList=self.getFileList(timestamp)
        
        i=len(self.fileList)-1
        while i > 0:
            if self.fileList[i].timestamp < timestamp:
                break
            else:
                i = i - 1
                
        while len(rv) < abs(n) and i >= 0 and i < len(self.fileList):
            m = direction * (abs(n)-len(rv))
            #print ("left:", m)
            x = self.fileList[i].read(timestamp,m)
            #print("dp.read extends by %s " % str(x))
            rv.extend(x)
            #print("dp.read after extend rv = %s " % str(rv))
            
            i = i + direction
        
        return rv
            
            
    #----------------------------------------------------------------------------------------------------
    #
    #  archiveDPClass::write()
    #
    @logged(logging.DEBUG)
    def write(self, desc, value, unit, timestamp):
        rv = 0        
        # check which file to use:
        if len (self.fileList) == 0:
            self.fileList=self.getFileList(timestamp)
        rv = HEADERERROR
        if self.fileList[-1].fileSize < int(globals.gConfig.archiveSplit):  #otherwise split file after 1MB
            rv =  self.fileList[-1].write(desc, value, unit, timestamp)   # can also return HEADERRERROR
            
        if HEADERERROR == rv :
            #try a new file probably data has changed the recordsize or need a new file or something else...
            ####have to close old file!!!
            
            fi = self.getNewFilename(timestamp)
            logging.debug ("ARCHIVE: Datapoint %s switch or new archiveFile %s" % (self.dp, fi))
            self.fileList.append(archiveFileClass(fi, self.dp))
            rv =  self.fileList[-1].write(desc, value, unit, timestamp)

        return rv

    #----------------------------------------------------------------------------------------------------
    #
    #  archiveDPClass::getInfo()
    #    returns a tuple of information:
    #       desc, unit, timestampfrom-to,  dataType, NumberOfEntries, dp
    #
    @logged(logging.DEBUG)
    def getInfo(self):
        rv= [ "", "", None, None, None, 0, ""]
        
        # open files:
        if len (self.fileList) == 0:
            self.fileList=self.getFileList(datetime.datetime.now())
        for file in self.fileList:
            if file is not None:
                fi =  file.getInfo()
                print ("archive.getInfo: file.getinfo is " + str(fi))
                desc, unit, timestampFrom, timestampTo, dataType, numberOfEntries, dp = fi
                rv[0] = desc
                rv[1] = unit
                if timestampFrom is not None:
                    if rv[2] is None or rv[2]>timestampFrom:
                        rv[2]=timestampFrom
                    
                if timestampTo is not None:
                    if rv[3] is None or rv[3]<timestampTo:
                        rv[3]=timestampTo

                rv[4] = dataType
                rv[5] += numberOfEntries
                rv[6] = dp
                
        return rv
     
#----------------------------------------------------------------------------------------------------
# ist der container für die archive DP klasse, verwaltet Liste von archiveDPClass
#
class archiveClass:
    def __init__(self):        
        self.archiveDPs = dict()   # dict of archiveDPClass instances, key is dp
        pass

    def __repr__ (self):
        s="Object  archiveClass"
        return s

#closes all open archiveDPClass (and files)
    def close(self):
        for x in self.archiveDPs.values():
            x.close()            
        pass

#flushes all open archiveDPClass (and files)
    def flush(self):
        for x in self.archiveDPs.values():
            x.flush()
        pass
        
    #----------------------------------------------------------------------------------------------------
    # Summenhaeufigkeit
    # actually the time per data spent below this value
    #----------------------------------------------------------------------------------------------------
    def calcSU(self, data, baseTimestamp):
        rv = list()
        if len(data)> 0:

            currtimestamp = data[0][0]
            #create new array with value and duration (timestamp not important)
            datDur=list()
            for d in data:
                duration=d[0] - currtimestamp
                datDur.extend( [[duration, d[1] ]])
                currtimestamp = d[0]
            
            #sort data by value
            datDur.sort(key=itemgetter(1))
            
            curValue= datDur[0][1]
            curDur = datetime.timedelta(0)
            
            #compress duplicates        
            for d in datDur:
                if d[1] == curValue:
                    curDur += d[0]
                else:
                    rv.extend( [[baseTimestamp, curValue, curDur]])
                    curValue = d[1]
                    curDur = d[0]
                    
            rv.extend ([[baseTimestamp, curValue, curDur]])        

        return rv
        
    #----------------------------------------------------------------------------------------------------
    #   INTEGRAL *dt
    #    integriert über die gesamte periode
    #----------------------------------------------------------------------------------------------------
    def calcINT(self, data, baseTimestamp):
        rv = list()
        if len(data)> 0:
            integral=0
            lastdat=data[0][1]
            lastdate=data[0][0]
            for d in data:
                if lastdate != 0:
                    val=d[1]-lastdat
                    tdif = (d[0] - lastdate).total_seconds()/60/60
                    if tdif != 0:
                        integral=integral + val*tdif
                    lastdat=d[1]
                    lastdate=d[0]
                    
            rv.extend([[baseTimestamp, integral, data[0][0], lastdate]]) #periode ueber die integriert wird angeben!
        
        return (rv)    
        
    #----------------------------------------------------------------------------------------------------
    #
    #----------------------------------------------------------------------------------------------------
    def calcSUM(self, data, baseTimestamp):
        rv = list()
        if len(data)> 0:
            sum = 0
            for d in data:
                sum = sum + d[1]
            rv.extend([[baseTimestamp, sum, data[0][0]]])
        
        return (rv)
        
    #----------------------------------------------------------------------------------------------------
    #  DIFFERENTIAL /dt
    #----------------------------------------------------------------------------------------------------
    def calcDIF(self, data, baseTimestamp):
        rv = list()
        if len(data)> 0:
            lastdat=data[0][1]
            lastdate=data[0][0]
            for d in data:
                if lastdate != 0:
                    val=d[1]-lastdat
                    tdif = (d[0] - lastdate).total_seconds()/60/60
                    if tdif != 0:
                        rv.extend([[d[0], val/tdif]]) #basetimestamp ist sinnlos...
                    lastdat=d[1]
                    lastdate=d[0]
        
        return (rv)    
        
    #----------------------------------------------------------------------------------------------------
    #
    #----------------------------------------------------------------------------------------------------
    def calcMAX(self, data, baseTimestamp):
        rv = list()
        if len(data)> 0:
            max=  -1e99
            maxdate=0            
            for d in data:
                if max < d[1]:
                    max = d[1]
                    maxdate = d[0]
            rv.extend([[baseTimestamp, max, maxdate]])
        
        return (rv)    
    #----------------------------------------------------------------------------------------------------
    #
    #----------------------------------------------------------------------------------------------------
    def calcMIN(self, data, baseTimestamp):
        rv = list()
        if len(data)> 0:
            min=1e99
            mindate=0            
            for d in data:
                if min > d[1]:
                    min = d[1]
                    mindate = d[0]
            rv.extend([[baseTimestamp, min, mindate]])
        
        return (rv)
    #----------------------------------------------------------------------------------------------------
    #
    #----------------------------------------------------------------------------------------------------
    def calcAVG(self, data, baseTimestamp):
        rv = list()
        if len(data)> 0:
            sum = 0
            for d in data:
                sum = sum + d[1]
            rv.extend([[baseTimestamp, sum/len(data), data[0][0]]])
        
        return (rv)

    #----------------------------------------------------------------------------------------------------
    #
    #----------------------------------------------------------------------------------------------------
    def calcDELTA(self, data, baseTimestamp):
        rv = list()
        #print ("calcDelta gets " + str(data))        
        
        last = len(data)
        if last > 1: # for a delta i need at least 2
            fromval=data[0][1]
            toval= data[last-1][1]
            print("  calculate from %f to %f (%s to %s)"%(fromval, toval, data[0][0], str(data[last-1][0])))
            rv.extend([[baseTimestamp, toval-fromval, data[last-1][0]]])
        elif last > 0:
            rv.extend([[baseTimestamp, 0.0, data[last-1][0]]])  #single value has no delta -> dummy zero
        else:
            rv.extend([[baseTimestamp, 0.0, baseTimestamp]])    #dummy zero value with default date.
        
        return rv
        
    #----------------------------------------------------------------------------------------------------
    #
    #           x "SU" : Summenhaeufigkeit
    #           x "INT": Integral (über die Zeit) (e.g. power -> energy)
    #           x "SUM", 
    #           x "MAX", "MIN", "AVG"
    #           geht auch ohne periode:
    #           "DELTA", : Summe, delta (zw. 2 werte, erkennt spruenge), 
    #           "DIF": Differential (d/dt)      (e.g. energy -> power)
    #
    #
    #
    #
    #----------------------------------------------------------------------------------------------------
    def  calculate1(self, data,oper, baseTimestamp):
    
        rv = list()
        
        if "SU" == oper:   #summenhäufigkeit 
           # liefert tupel: ende-timestamp, wert, sekunden über dem Wert, sortiert nach wert
           # alle vorhandenen werte mit dem selben Timestamp
           rv.extend(self.calcSU(data, baseTimestamp))
        elif "SUM" == oper: # flache Summe: 
           # liefert ende-timestamp, summe aller werte
           rv.extend(self.calcSUM(data, baseTimestamp))
        elif "DELTA" == oper: # delta zwschen 2 werten
           # ende - anfang
           rv.extend(self.calcDELTA(data, baseTimestamp))
        elif "INT" == oper: # Integral (Leistung -> Energie)
           # ende-time-stamp, integral bis dahin
           rv.extend(self.calcINT(data, baseTimestamp))
        elif "DIF" == oper: # Differential (Energie -> Leistung)
           # ende-time-stamp, Differential
           rv.extend(self.calcDIF(data, baseTimestamp))
        elif "MAX" == oper: # Maximum
           # 
           rv.extend(self.calcMAX(data, baseTimestamp))
        elif "MIN" == oper: # Minimum (ohne NULL?)
           # 
           rv.extend(self.calcMIN(data, baseTimestamp))
        elif "AVG" == oper: # flacher durchschnitt
           # 
           rv.extend(self.calcAVG(data, baseTimestamp))
        else:
           logging.error("Archiv read: unknown operator: %s " % (oper))

        #print ("Calculate1 %d, %s, returns %s" % (len(data), oper, str(rv)))

        return rv

    #----------------------------------------------------------------------------------------------------
    #
    # calculate Oper bekommt eine daten einer Periode
    #
    #
    #
    #----------------------------------------------------------------------------------------------------
    def calculateOper(self, dp, oper, timestampFrom, timestampTo):
    
        #print ("calculateOper tries from %s to %s " % (str(timestampFrom), str(timestampTo)))    
        rv = list()
        
        #immer von hinten nach vorne...
        if timestampTo < timestampFrom:
            x = timestampTo
            timestampTo = timestampFrom
            timestampFrom = x
            
        blocksize = 60
    
        data = list()
        timestamp=timestampFrom
        while True:
            d = self.archiveDPs[dp].read(timestamp, blocksize)
            #print ("CalculateOper read got %d records: %s" % (len(d), str(d)))
            
            if len(d)== 0 or d[0][0] == timestamp:
                # statt nix kriege ich dann immer das letzte zurueck
                break
                
            for x in d:
                if x[0] <= timestampTo:
                    data.extend([x])  #x ist schon eine Liste, d.h. ich moechte eine liste von listen
                    
            timestamp = d[len(d)-1][0]
            #print ("CalculateOper restart at %s" %(timestamp))
            
            if timestamp > timestampTo:
                break
           
        rv = self.calculate1(data,oper,timestampFrom)

        #print ("CalculateOper returns %s" % (str(rv)))
          
        return rv
        
    #----------------------------------------------------------------------------------------------------
    # archiveClass::read 
    #    if timedelta is supplied, the time difference in seconds between each 2 successive returned values is
    #    timedelta
    #    spezialbehandlung, wenn anzahl = 0,5 wird nix zurückgeliefert wenn nix neues da ist, sonst
    #    wird der letzte bekannte wert zurückgeliefert
    #    operation bezieht sich auf timeDelta intervalle: one of:
    #           "SU" : Summenhaeufigkeit
    #           "SUM", "DELTA", : Summe, delta (zw. 2 werte, erkennt spruenge), 
    #           "INT": Integral (über die Zeit) (e.g. power -> energy)
    #           "DIF": Differential (d/dt)      (e.g. energy -> power)
    #           "MAX", "MIN", "AVG"
    #
    @logged(logging.DEBUG)
    def read(self, dp, timestamp, m, timeDelta = None, operation = None, timeStampTo = None):

        rv = list()
    
        n=m
        if 0.5 == n:
            n=2
        
        if dp not in self.archiveDPs:
            self.archiveDPs[dp] = archiveDPClass(dp)        
            
        if timestamp is None:
            timestamp = datetime.datetime.now()
                
        if timeDelta is None:
            timeDelta = 0            

        if timeDelta != 0 :   #only specific values
            if n < 0:
                n = -1 * n
                timeDelta = -1 * timeDelta
                
            if timeStampTo is None:
                if timeDelta > 0:
                  timeStampTo = timestamp + datetime.timedelta(days = 36500)
                else:
                  timeStampTo = timestamp - datetime.timedelta(days = 36500)
                
            if operation is None:
                while n > 0:            
                    data=self.archiveDPs[dp].read(timestamp, 1)
                    if len(data) > 0:
                        for d in data: #sollte zwar nur 1 kommen...
                            if timeDelta > 0:
                                if timestamp >= timeStampTo:
                                    n=0
                            else:
                                if timestamp <= timeStampTo:
                                    n=0
                                    
                            if n > 0:        
                                rv.extend([[timestamp, d[1], d[0]]]) #nominelle zeit als erstes...
                    n -= 1
                    timestamp = timestamp + datetime.timedelta(seconds = timeDelta)
            else: #alle werte mit operation betrachten:
                while n > 0:
                    timestampTo = timestamp + datetime.timedelta(seconds = timeDelta)
                    x = self.calculateOper(dp, operation, timestamp, timestampTo)
                    #print ("calcOper returns %s " % repr(x))
                    rv.extend(x) # liefert nur eine liste zurueck, brauche aber liste von listen.
                    n-=1
                    timestamp=timestampTo
                    if timeDelta > 0:
                        if timestamp >= timeStampTo:
                            n=0
                    else:
                        if timestamp <= timeStampTo:
                            n=0

        else:
            #5sek einbremsen, wenn ich nur einen eintrag will (kommt offenbar von einem Javascript browser)
            i = 5

            while  i > 0:
                i -= 1
                rv = self.archiveDPs[dp].read(timestamp, n)
                    
                #spezialbehandlung für 0.5 nicht den letzten zurückliefern sondern warten und dann ev. nix                            
                if 0.5 != m:
                    break

                if len(rv) > 1:
                    #es gibt wirklich neuen wert
                    #nur den neuen zurückliefern:
                    rv = rv[1:]
                    break
                    
                #wieder loeschen
                rv = list() #wenn 0 ==i dann wird der Wert zurückgegeben.            
                time.sleep(1)
                
        #print ("archiveRead returns %s" % (str(rv)))        
                
        return rv
    
    #----------------------------------------------------------------------------------------------------
    #
    #  archiveClass::getInfo()
    #    returns a tuple of information:
    #       desc, unit, timestampfrom-to, dataType, NumberOfEntries, 
    #
    @logged(logging.DEBUG)
    def getInfo(self, dp):

        if dp not in self.archiveDPs:
            self.archiveDPs[dp] = archiveDPClass(dp)        
        
        rv = self.archiveDPs[dp].getInfo()
        return rv
    
    #-------------------------------------------------------------------------------------------------
    # getDatapoints: returns list of datapoints 
    # cached:
    #  
    def getDatapoints(self):
    
        rv = globals.archiveCache.get("getDataPoints", self.raw_getDatapoints, 86400) # the list of datapoints shall change only once a day.
        return rv

    #-------------------------------------------------------------------------------------------------
    # raw getDatapoints: returns list of datapoints 
    #  
    def raw_getDatapoints(self, dummyForCache):
    
        rv = list()

        #getFileName provides base path.
        #mod_ttyusb_modbus_2_zaehler_systempower-2017-01-31_21.02.20.pvOpt

        formatStringTS = "-2???-??-??_??.??.??" + globals.gConfig.archiveext
        prefix = getFileName("") 
        
        searchName = prefix + "*" + formatStringTS
        fileNames = glob.glob(searchName)
        zeroLen = list()
        # use only file greater than 40 bytes (header + some data)
        for f in fileNames:
            size = os.path.getsize(f)
            #print ("size of %s is %s " % (f, repr(size)))
            
            if size < 40:
                #print("to be removed file due to filezise %s " % f)
                zeroLen.append(f)
                #fileNames.remove(f)
        
        for f in zeroLen:
            #print("remove file due to filezise %s " % f)
            fileNames.remove(f)
            
        dpNames = { x[len(prefix) : - len(formatStringTS) ] : x for x in fileNames} #trim timestamp
        fList = list(set(dpNames.values())) #distinct datapoints

        #print("dpNames is  %s " % repr(dpNames))
        #print("fList is  %s " % repr(fList))

        #rv.append (["found %d datapoints" % len(fList), "", None, None, None, 0, ""])
        for fn in fList:
            archiveFile = archiveFileClass(fn, "")   # dp habe ich nicht, krieg ich aus header
            fileInfo = archiveFile.getInfo()
            archiveFile.close()
            
            #print("fileInfo of filename %s is %s " % (fn, repr(fileInfo)))

            
            #rv.append(dpNames[fn])
            #rv.append("-".join([str(s) for s in fileInfo]))
            #if len(fileInfo[0]) == 0: #no description
            #    fileInfo[0] = ">>" + fileInfo[6] # use dp
            #if len(fileInfo[0]) == 0: #no dp either
            #    fileInfo[0]="?? " + fn
            
            if isinstance(fileInfo[0], str) and isinstance(fileInfo[6], str):
                if (len(fileInfo[0]) != 0) and (len(fileInfo[6]) != 0):
                    rv.append(fileInfo) #ignore invalid archive files.

        rv = sorted(rv, key=lambda kv: kv[0].lower())
        
        return rv

    
    #----------------------------------------------------------------------------------------------------
    # write
    # [name, ]
    # 
    @logged(logging.DEBUG)
    def write(self, data):
    #dp, unit, timestamp, dataToWrite):
    
        rv = False
    
        if list == type(data) or tuple == type(data):
            if len(data) > 4:            #ignore everything else!
                status="Ok"
                if len(data) > 5:
                    status=data[5]
                    
                if status=="Ok":
                    
                    rv=False
                    
                    try:
                        desc=data[0]
                        value=data[1]
                        unit=data[2]
                        timestamp=data[3]
                        dp=data[4]

                        if dp not in self.archiveDPs:
                            self.archiveDPs[dp] = archiveDPClass(dp)        
                        
                        rv = self.archiveDPs[dp].write(desc, value, unit, timestamp)
                    except Exception as e:
                        logging.exception("cannot add data to archive: data wrong %s" % repr(data))
                else:
                    logging.debug("archive.write: don't write status not Ok (status = %s)" % (status))
            else:
                logging.error("archive.write: got not enouth data expect at least len 5 (got len = %d)" % (len(data)))
        else:
            logging.error("archive.write: got wrong data %s " %(str(type(data))))

        return rv

        

#----------------------------------------------------------------------------------------------------
# Buffer conversion helper functions:
#
#
def timeToBuf(t):
    f=time.mktime(t.timetuple())
    return (floatToBuf(f))
        
def bufToTime(buf):

    zeroTime = datetime.datetime.fromtimestamp(0.0)


    rv = datetime.datetime.fromtimestamp(0.0)    
    try:    
        f=bufToFloat(buf)
        rv = datetime.datetime.fromtimestamp(f)
        if zeroTime == rv:
            rv = None
    except Exception as e:
        logging.exception("unable to convert to datetime")
        rv = None        

        
    return  rv

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
        s="decode-error???"        
    return s

def floatToBuf(f):
    return struct.pack(FFMT,f)

def bufToFloat(buf):
    return struct.unpack(FFMT, buf)[0]

def intToBuf(i):
    return struct.pack(IFMT,i)
    
def bufToInt(buf):
    return struct.unpack(IFMT, buf)[0]
    
def boolToBuf(i):
    return struct.pack(BFMT,i)
    
def bufToBool(buf):
    return struct.unpack(BFMT, buf)[0]
        

def xToBuf(value):
    rv = None
    if type(value) == str:
        rv = stringToBuf(value)
    elif type(value) == float:
        rv = floatToBuf(value)
    elif type(value) == int:
        rv = intToBuf(value)
    elif type(value) == bytes:
        rv = value
    elif type(value) == bool:
        rv = boolToBuf(value)
    else:
        rv = stringToBuf("Unknown type %s " % repr(type(value)))
        
    return rv


    
#----------------------------------------------------------------------------------------------------
# readString:
#

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
# getFileName:
#    returns name according to dp (without datetime-postfix)
#
@logged(logging.DEBUG)
def getFileName(dp):
    #substitute everything that could disturb a filename 
    nonChars =".,;:<>|/\\!§$%&/()=\"^°+*#\'"
    rv = dp.lower()
    for ch in nonChars:
        rv = rv.replace(ch, "_")
    # and append basic path:
    
    rv = globals.gConfig.archivepath + rv  
    
    return rv
    
#----------------------------------------------------------------------------------------------------
# escape_glob:
#    got from https://bugs.python.org/issue8402
#
@logged(logging.DEBUG)
def escape_glob(path):
    transdict = {
            ' ': '[ ]',
            '[': '[[]',
            ']': '[]]',
            '*': '[*]',
            '?': '[?]',
            }
    rc = re.compile('|'.join(map(re.escape, transdict)))
    return rc.sub(lambda m: transdict[m.group(0)], path)
    

#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main():    
  with config.configClass() as configuration:
    globals.config=configuration
    
    arch = archiveClass()
    
    if False:
        #dp="PV/PV0/DAY_ENERGY"    
        dp="TEMP/00042b8679ff"
        #dp="DLMS/z/2.8.0"
        
        #dp = "ETH/kellerschalter"

        for i in range(1,6):
            data=driverCommon.read1(dp)
            print (data)        
            arch.write(data)
            time.sleep(5)
            
        # und jetzt rücklesen:
        data=arch.read(dp, datetime.datetime.now(), -1000) # 1000 werte zurueck from now:
        print ("Archive of dp %s is " % dp)
        for d in data:
            print("%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), repr(d[1])))    
            
    if False:
        dat = arch.read ("comp_pvtotal_p[0]_p[1]__pv_pv0__ _pv_pv1_", datetime.datetime.now(), -20)
        print ("archive read returns ", dat)

    if False:
        dp="PV/PV0/PAC"
        dat = arch.getInfo (dp)
        print ("archive getInfo returns ", dat)
        data=arch.read(dp, datetime.datetime.now(), -20, 0)
        print ("Archive of dp %s is " % dp)
        for d in data:
            print("%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), repr(d[1])))    

    if False:
        #dp="PV/PV0/YEAR_ENERGY"
        dp="DLMS/ttyUSB.irKopf/1.8.0"
        dat = arch.getInfo (dp)
        print ("archive getInfo returns ", dat)
        data=arch.read(dp, datetime.datetime.now(), 20, -60*60*24, "AVG") 
        print ("Archive average of dp %s is " % dp)
        #print ("main: read got %s" % data)
        for d in data:
            s = ", " + repr(d[1:])
            print("%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), repr(s)))
            
    if False:
        #dp="PV/PV0/YEAR_ENERGY"
        dp="DLMS/ttyUSB.irKopf/1.8.0"
        data=arch.read(dp, datetime.datetime.now(), 20, -60*60*24, "SUM") 
        print ("Archive SUM of dp %s is " % dp)
        #print ("main: read got %s" % data)
        for d in data:
            s = ", " + repr(d[1:])
            print("%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), repr(s)))
        
    if False:
        #dp="PV/PV0/YEAR_ENERGY"
        dp="DLMS/ttyUSB.irKopf/1.8.0"
        data=arch.read(dp, datetime.datetime.now(), 20, -60*60*24, "MAX") 
        print ("Archive MAX of dp %s is " % dp)
        #print ("main: read got %s" % data)
        for d in data:
            s = ", " + repr(d[1:])
            print("%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), repr(s)))

    if False:
        #dp="PV/PV0/YEAR_ENERGY"
        dp="DLMS/ttyUSB.irKopf/1.8.0"
        data=arch.read(dp, datetime.datetime.now(), 20, -60*60*24, "MIN") 
        print ("Archive MIN of dp %s is " % dp)
        #print ("main: read got %s" % data)
        for d in data:
            s = ", " + repr(d[1:])
            print("%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), repr(s)))
        
    if False:
        #dp="PV/PV0/YEAR_ENERGY"
        dp="DLMS/ttyUSB.irKopf/1.8.0"
        data=arch.read(dp, datetime.datetime.now(), 20, -60*60*24, "DIF") 
        print ("Archive DIF of dp %s is " % dp)
        for d in data:
            s = ", " + repr(d[1])
            print("%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), repr(s)))
        
    if False:
        #dp="PV/PV0/YEAR_ENERGY"
        #dp="DLMS/ttyUSB.irKopf/1.8.0"
        dp="TEMP/00042b8679ff"
        #dp="ETH/Kueche/A2" #brenner
        dat = arch.getInfo (dp)
        print ("archive getInfo returns ", dat)
        data=arch.read(dp, datetime.datetime.now(), 20, -60*60*24, "SU") 
        print ("Archive SU of dp %s is " % dp)
        for d in data:
            s = ", " + repr(d[1]) + ", " + repr(d[2].total_seconds()) + " seconds"
            print("%s;  %s" %(d[0].strftime("%Y/%m/%d %H:%M:%S"), s))
            
    if True:
        data = arch.getDatapoints()
        for d in data:
            print ("<<%s / %s>>" % (repr(d[0]), d[1]))
            
    arch.close()

    return 0
    
        
if __name__ == "__main__":
    with config.configClass() as configuration:
        globals.gConfig= configuration
        main()
