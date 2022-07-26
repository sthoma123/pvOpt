#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# replaces cosem.py, uses cosemDecrypt.c to do the encryption stuff
#
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
#
#

print ("imported " + __name__)

import serial, time
import socket
import struct
from ctypes import *
import binascii

import globals
import config
import collections
import configparser
import logging
import dpLogger
import dpLogger

from helpers import printError
from helpers import bcolors
						
gcmD = CDLL("./gcmDecrypt/gcmDecrypt.so") 

def unused4 (by, dataDict):
    return unused(by, 4)

def unused2 (by, dataDict):
    return unused(by, 2)

def unused1 (by, dataDict):
    return unused(by, 1)

def unused (by, n):
    return n, ''.join('{:02x}'.format(x) for x in by[0:n])
    
def hex1str(by, dataDict):
    return 1, '{:02x}'.format(by[0])
    
def int1(by, dataDict):
    return 1, intN(by,1)
    
def hex2str(by, dataDict):
    return 2, hexNstr(by,2)

def hex3str(by, dataDict):
    return 3, hexNstr(by,3)

def hex4str(by, dataDict):
    return 4, hexNstr(by,4)

def hex6str(by, dataDict):
    print ("hex6str got %s " % str(by))
    return 6, hexNstr(by,6)
    
def hex8str(by, dataDict):
    return 8, hexNstr(by,8)
    
def hex11str(by, dataDict):
    return 11, hexNstr(by,11)

def hex12str(by, dataDict):
    return 12, hexNstr(by,12)

def str3str(by, dataDict):
    return 3, strNstr(by, 3)
    
def str8str(by, dataDict):
    return 8, strNstr(by, 8)
    
def strNstr(by, num):    
    try:
        s=by[0:num].decode('utf-8')
    except Exception as e:
        t="strNstr(%d) got error %s" % (num,str(e))
        #dpLogger.log(logBuffer, "Exception", t)
        printError (t)
        
        s="unknown"       
    return s

def hexNstr(by, num):
    s=""
    if not(len(by) < num):
        for j in range(0,num):
            s += '{:02x} '.format(by[j])
    return s

def intN(by, num):
    i=0
    if not(len(by) < num):
        for j in range(0,num):
            i=256*i+by[j]
    return i

def int4str(by, dataDict):
    return 4, "%08d"%intN(by,4)

def int2str(by, dataDict):
    return 2, "%04d"%intN(by,2)

def int1str(by, dataDict):
    return 1, "%02d"%intN(by,1)

def hdlcPayload(by, dataDict):
    # here comes the AES decryption.
    # len of bby should be 1 more than the AES part (stop-byte), currently fixed 92 bytes...
    # or 77 or 79
    #l = len(by) -15
    #if l != 77:
    #    printError ("AES Framelength is %d; expected %d" % (l, 77))

    l=dataDict["lengthRemaining"][0] - 17  #(len securitybyte(1) + sequence (4) + auth(12), final crc and stopbyte belongs to hdlcframe    
    if not(l  == (len(by) - 17)):
        printError ("payload Framelength is %d; expected %d" % (l, len(by)))
    
    print("payload got len: %d, %s" % (l, str(by[0:l])))
    return l, by[0:l]

def hdlcContent(hdlcFrame, hdlcPattern):
    return 1

def destAddr(by, dataDict):  #one two or four bytes depending on msb (set bit means finish)
    rv=by[0:1]
    if (rv[0] & 0x01) == 0:
        rv=by[0:2]
        if (rv[1] & 0x01) == 0:
            rv= by[0:4]
            
    addrLen = len(rv)
    return addrLen, hexNstr(rv, addrLen)

weekdayDict = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}
monthDict = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
    }
def weekday(by, dataDict):
    i = int(by[0])
    if i > 7 or i < 1:
        printError ("Warning: wrong weekday index %d" % i)
        return 1, ""
    else:
        return 1, weekdayDict[i]
    
def month(by, dataDict):
    i = int(by[0])
    if i > 12 or i < 1:
        printError ("Warning: wrong monthindex index %d" % i)
        return 1, ""
    else:
        return 1, monthDict[int(by[0])]
    
def hms(by, dataDict):
    return 3,"%02d:%02d:%02d" % (int(by[0]), int(by[1]), int(by[2]))


#4B 46 4D 33 30 31 33 31 36 36 33 39 30 30 30 34 COSEM Logical number
#09 06 
#00 11 19 09 00 FF OBIS Code
#06 
#00 00 00 3A Energie +
#06 
#00 00 00 00 Energie -
#06 
#00 00 00 10 Leistung +
#06 
#00 00 00 00 Leistung -
#06 
#00 00 00 00 R+
#06 
#00 00 00 08 R-
#----- AES Verschlüsselungsende
#18 4A CRC 
#7E  Ende


#static:
olddata=[]
olddata.extend(range(0,400))
olddataParsed=[]
olddataParsed.extend(range(0,400))
oldDataDecrypt=[]
oldDataDecrypt.extend(range(0,400))
old=[]
old.extend(range(0,20))
for i in range(0,20):
    old[i]=[]
    old[i].extend(range(0,400))


decryptedPattern=[   #content of decrypted payload, interpreted by hdlcPayload using parse function
    [hex6str, "unk1", ""],
    [int2str,"year","-"], #year
    [month,"mont","-"], #mont
    [int1str,"day",""], #day
    [weekday,"weekday",""], #weekday
    [int1str,"hour",""], #h:m:s
    [int1str,"min",""], #h:m:s
    [int1str,"sec",""], #h:m:s
    [unused4,"un1",")"], #millisec, 2bytes TZ offset, clockstate
    [hex2str,"un2",")"], #
    [hex1str,"un3",")"], #
    [int2str,"32.7.0","V"], # Spannung L1
    [hex1str,"un4",")"], #
    [int2str,"52.7.0","V"], # Spannung L2
    [hex1str,"un5",")"], #
    [int2str,"72.7.0","V"], # # Spannung L2
    [hex1str,"un6",")"], #
    [int2str,"31.7.0","A"], # # 
    [hex1str,"un7",")"], #
    [int2str,"51.7.0","A"], # # 
    [hex1str,"un8",")"], #
    [int2str,"71.7.0","A"], # # 
    [hex1str,"un9",")"], #
    [int4str,"1.7.0","W"], # wirkleistung bezug momentan
    [hex1str,"un10",")"], #
    [int4str,"2.7.0","W"], # wirkleistung einsp momentan
    [hex1str,"un11",")"], #
    [int4str,"1.8.0","Wh"], #
    [hex1str,"un12",")"], #
    [int4str,"2.8.0","Wh"], #
    [hex1str,"un13",")"], #
    [int2str,"phaseDeviation1","Deg"], # # 
    [hex1str,"un14",")"], #
    [int2str,"phaseDeviation2","Deg"], # # 
    [hex1str,"un15",")"], #
    [int2str,"phaseDeviation3","Deg"], # # 
    [hex2str,"CRC",""], #
    [str8str,"serialNumber",""] #
]

#describe HDLC Syntax:
# contains list of lists containing (interpreter function, name, unit)
#
pattern=[
    [hex1str, "start", ""],
    [hex1str, "HDLCframeType", ""],
    [int1, "length", ""],
    [destAddr, "destAddr", ""], #1, 2 or 4 bytes
    [hex1str, "sourceAddr", ""],
    [hex1str, "controlField", ""],
    [hex2str, "header ControlSequence", ""],
    [hex3str, "LLC frame header", ""],
    [hex2str, "unknown2", ""], #can be kind of CRC
    [hex8str, "systemTitle", ""], #printeable "LGZ and serial number"
    [int1, "lengthRemaining", ""],
    [hex1str, "securityByte", ""], #0x30
    [hex4str, "sequence", ""],
    [hdlcPayload, "encrypted", ""],
    [hex12str, "AuthTag", ""],  # needed for decryption.
    [hex2str, "HDLCcrc", ""],
    [hex1str, "stop", ""]
   ]

#-------------------------------------------------------

cosemExTimeout   =1
cosemFrameLength = 2
cosemWrongStop = 3
cosemWrongStart = 4
cosemNoStart = 5
cosemNoStop = 6


def toBin(hex):
    bi = binascii.unhexlify(hex.replace(" ", ""))
    return bi
    
#-----------------------------------------------------------------------------------------------------------
def toHex(cont):
    s = ""
    i=0
    while i<len(cont):
        by=cont[i:i+1]
        l,t=hex1str(by, {})
        s += t
        i += l

    return s


class cosemException(Exception):
    errId=0
    reason=""
    def __init__(self, errId, reason):
        self.reason = reason
        self.errId = errId
    def __str__(self):
        return "cosemException ID is %s, %s" % (repr(self.errId), repr(self.reason))

class cosem(object):

    logBuffer = []
        
    def __init__(self, serial_port = "ttyUSB.irKopf"):
        
        self.ser = serial.Serial(
            port = "/dev/" + serial_port,
            baudrate = 9600,
            bytesize = serial.EIGHTBITS,
            parity = serial.PARITY_NONE,
            timeout = 3.0) #actually timeot is max 1.5s between chars and 2.2s after id message

    def gcmAESdecrypt(self, data, key, auth):  #data as dictionary key and auth as bytes
    
        reason=""
        global gcmD
        
        #from: https://github.com/chester4444/3pter
        #  // copy IV (initialization vector)
        #  hex2bin(payloadptr, 8, gcm_iv);
        #  hex2bin(&payloadptr[20], 4, &gcm_iv[8]);
        #
        #  // copy ciphertext
        #  hex2bin(&payloadptr[28], 77, gcm_ct); 
        #
        #  // copy auth tag
        #  hex2bin(&payloadptr[182], 12, gcm_tag); 
        #AES-128-GCM
        # • initalization vector (IV = system-title + nonce) – 12 bytes
        iv  = toBin(data["systemTitle"][0])        #8
        iv += toBin(data["sequence"][0])          #4  -> 12
        
        #• autentication tag (T) – 12 bytes
        tag = toBin(data["AuthTag"][0])           #12
        #tag += binascii.unhexlify(data["stop"][0].replace(" ", ""))             #1 -> 12
        
        #• additional auth. data (AAD = security-byte+auth key) – 17 bytes
        aad = toBin(data["securityByte"][0])     #1
        aad += auth                                    #16-> 17
                
        # ciphertext (C) – 77 bytes (79, 92)
        ciphertext = data["encrypted"][0]

        print("ciphertext = %s" % (self.sprintHex(ciphertext,old[5])))
        print("AADat= %s" % (self.sprintHex(aad,old[4])))
        print("tag  = %s" % (self.sprintHex(tag,old[3])))
        print("key  = %s" % (self.sprintHex(key,old[0])))
        print("iv   = %s" % (self.sprintHex(iv,old[6])))
        
        bCiphertext = create_string_buffer(ciphertext, len(ciphertext))
        bAad = create_string_buffer(aad, len(aad))
        bTag = create_string_buffer(tag, len(tag))
        bkey = create_string_buffer(key, len(key))
        bIv =  create_string_buffer(iv, len(iv))
        bPlaintext = create_string_buffer(b" "*len(ciphertext), len(ciphertext))  #length must be the same as ciphertext

        print("python passes ciphertext: %s " % str(ciphertext))

        rv = gcmD.gcm_decrypt(
                    bCiphertext, len(ciphertext),
                    bAad, len(aad),
                    bTag,
                    bkey,
                    bIv, len(iv),
                    bPlaintext)
                 

        if rv == 0 :
            reason="gcmDecrypt: authentification failed"
            
        print ("gcm_decrypt authentification %s" % ("successful" if rv > 0 else "Failed"))
        print ("returns %d plaintext: %d %s" % (rv, sizeof(bPlaintext), repr(bPlaintext.raw)))
        
        data["decrypted"]=[bytes(bPlaintext.raw), ""]
        
        if not(reason==""):
            dpLogger.log(logBuffer, "cosemDecrypt", reason)
            rv["Reason"]=reason
       
        return rv

    def speedFromChar(self, speed):
        new_baud_rate = 300  # default
        if (speed == "1"): new_baud_rate = 600
        elif (speed == "2"): new_baud_rate = 1200
        elif (speed == "3"): new_baud_rate = 2400
        elif (speed == "4"): new_baud_rate = 4800
        elif (speed == "5"): new_baud_rate = 9600
        elif (speed == "6"): new_baud_rate = 19200
        return new_baud_rate

        
    def setSerBaudrate(self, speedChar):
        newBaudrate=self.speedFromChar(speedChar)
        #print ("Change to %d baud" % newBaudrate)
        self.ser.baudrate=newBaudrate
        

    def close(self):
        self.ser.close()
            
    def checkIfIdle(self, tox = 3.5):
        timSaf=self.ser.timeout
        self.ser.timeout = tox
        x=b'x'
        buf = ""
        #print ("Waiting for silence")
        while True:            
            x = self.ser.read(1)
            if len(x) == 0:
                break
        #print ("silent Ok.")
        
        self.ser.timeout = timSaf
        return (0)
                
#-----------------------------------------------------------------------------------------------------------
    def timedQuery(self):
        rv = bytearray(b'')
        while True:
            x = self.ser.read(1)
            if 0 == len(x): #timeout (1 sec)
                break
            else:
                rv.append(x[0])
                
        return bytes(rv)

#-----------------------------------------------------------------------------------------------------------
    def printHex(self, cont, olddata):
        s = self.sprintHex(cont, olddata)
        print ("%s" % (s))
        
#-----------------------------------------------------------------------------------------------------------
    def sprintHex(self, cont, olddata):        
        i=0
        s=""
        
        while i<len(cont):
            by=cont[i:i+1]
            l,t=hex1str(by, {})

            t = "%s " %(t)
            if olddata[i]!=t:
                s+=bcolors.FAIL + t + bcolors.ENDC
            else:
                s+=t + ""
            olddata[i]=t

            i+=l               
            
        s = "(%s) %s" % (len(cont),s)
        
        return s
        
    #------------------------------------------------------------------    
    # returns 0 if Ok.
    #
    def plausibilityCheck(self, cont, dataDict):
        
        rv = 0
        frameLen = len(cont) # should match length bytes
        reason=""
    
        #some plausibility checks:
        if "start" not in dataDict:
            reason="ParseError no frame start byte: Frame should start with 0x7e"
            dpLogger.log(self.logBuffer, "cosemDecrypt", reason)
            printError (reason)
            rv = 1
        else:
            if dataDict["start"][0] != '7e':
                reason="ParseError wrong frame start byte (%s instead of 7e)" % dataDict["start"][0]
                #   raise cosemException(cosemWrongStart, "ParseError wrong frame start byte (%s instead of 7e)" % dataDict["start"])
                dpLogger.log(self.logBuffer, "cosemDecrypt", reason)
                printError (reason)
                rv = 2
            else:   
                print ("ParseOk: Start Bytes Ok: %s" % str(dataDict["start"][0]))

        if "stop" not in dataDict:
            reason="ParseError no frame stop byte: Frame should stop with 0x7e"
            #raise cosemException(cosemNoStop, "ParseError no frame stop byte")
            dpLogger.log(self.logBuffer, "cosemDecrypt", reason)
            printError (reason)
            rv = 3
        else:
            if dataDict["stop"][0] != '7e':
                reason="ParseError wrong frame stop byte (%s instead of 7e)" % dataDict["stop"]
                dpLogger.log(self.logBuffer, "cosemDecrypt", reason)
                printError (reason)
                rv = 4
            else:
                print ("ParseOk: Stop Byte Ok: %s" % str(dataDict["stop"][0]))
        
        if "length" not in dataDict:
            reason="ParseError no length field in frame"
            dpLogger.log(self.logBuffer, "cosemDecrypt", reason)
            printError (reason)
            rv = 5
        else:
            if dataDict["length"][0]!= frameLen - 2:
                reason="ParseError: FrameLen does not match length in frame header %s != (%s - 2)" % (str(dataDict["length"][0]), str(frameLen))
                dpLogger.log(self.logBuffer, "cosemDecrypt", reason)
                printError (reason)
                rv = 6
            else:
                print ("ParseOk: length in Header matches framelength Ok: %s" % str(dataDict["length"][0]))
                
                
        if not ("" ==reason ):
            dataDict["Reason"]=reason
            
        return rv
        
        
#-----------------------------------------------------------------------------------------------------------
    def parse(self, rv, cont, pattern):
        
        byteCounter=0  #byte counter
        parseCounter = 0
        s=""
        reason=""            
        
        while byteCounter < len(cont):
            if not (parseCounter < len(pattern)):
                reason ="parse: WARNING: too much data (%d) for parser, parsecounter (%d) overflow" %(len(cont), byteCounter)
                break
                
            byteLen,t=pattern[parseCounter][0](cont[byteCounter:], rv) #call decoding function depending on byte index, parameter is second value
            rv[pattern[parseCounter][1]]= [t,  pattern[parseCounter][2]]  #[1] is name or what [2] is unit
            byteCounter+=byteLen
            
            parseCounter+=1
            
        #print ("rv = %s" % (str(rv)))
        if parseCounter<len(pattern):
            reason=("parse: WARNING: too little data for parser, parsecounter does not match patternlen")
            
            
        if not ("" ==reason ):
            dpLogger.log(self.logBuffer, "cosemDecrypt", reason)
            printError (reason)
            rv["Reason"]=reason

            
        return rv
        
    #----------------------------------------------------------------------------------------------------
    # main library entry, returns dict of read data:
    # try 3 times. (meter sends da3ta in 2sec intervalls. -> max 15sec delay
    #
    def tryQuery(self, buf):
        self.logBuffer = buf
    
        auth=bytes(bytearray.fromhex(globals.config.configMap["COSEM"]["AUTH"]))
        enc=bytes(bytearray.fromhex(globals.config.configMap["COSEM"]["ENC"]))

        #print ("keys are %s %s " %(str(enc), str(auth)))

        retry=3
        rv = dict()
        ok = False
        
        while retry > 0 and not ok:
            a=self.timedQuery()
            #a=b'\rv7e\rva0\rv76\rvce\rvff\rv03\rv13\rv3c\rv02\rve6\rve7\rv00\rvdb\rv08\rv4c\rv47\rv5a\rv67\rv72\rvaa\rv06\rvb6\rv5e\rv30\rv00\rv03\rvc1\rva5\rvff\rvd3\rv05\rvd0\rv59\rv05\rvfd\rvb6\rvfc\rve8\rv31\rv78\rva1\rv12\rv30\rv00\rve1\rv9e\rv99\rv97\rv3d\rv62\rv0e\rvbf\rv4f\rv60\rv5d\rv8d\rvb5\rv6f\rv9c\rvd9\rv06\rva7\rv50\rv99\rvf3\rv8a\rv2b\rv3c\rv8d\rv51\rv62\rv26\rv14\rv21\rvf6\rv15\rva0\rv92\rv76\rv45\rva9\rvc2\rva8\rv69\rvd0\rv2e\rveb\rv04\rv84\rv8c\rv3e\rv4c\rv3e\rva3\rv82\rv31\rvf5\rvb5\rv3d\rvcd\rva2\rvce\rv60\rv96\rv90\rvf1\rv05\rv77\rvf0\rvc7\rv9e\rv06\rvf6\rvca\rv8e\rvc9\rv06\rvfb\rv47\rv7e'
            #self.printHex(a, olddata)
            rv = dict()
            
            rv=self.parse(rv, a, pattern)
            if (0 == self.plausibilityCheck(a, rv)):        
                if "encrypted" in rv:
                    self.gcmAESdecrypt(rv, enc, auth) # returns empty array if not authenticated
                    if "decrypted" in rv:
                        data = rv["decrypted"][0]
                        #data.printHerv(data, encOldData)
                        
                        #decode decrypted data
                        if len(data) > 0:
                            rv=self.parse(rv,data,decryptedPattern)
                            ok = True
                            
            retry -= 1
            if not ok:
                dpLogger.log(self.logBuffer, "cosemDecrypt", "tryQuery: retry %d" % retry)
                
            
        if not ok:
            dpLogger.log(self.logBuffer, "cosemDecrypt", "tryQuery end-of-retries")

        return rv

            
def OBISTranslate(aData, OBISconfig):
    rv=""    
    if aData in OBISconfig["OBIS"]: # found direct translation
        rv = OBISconfig["OBIS"][aData]
    else:
        ds=aData.split(".")
        i=0
        while i < 3:
            if len(ds)>i:
                
                if ds[i] in OBISconfig["OBIS.%d" % (i+1)]:
                    rv = rv + OBISconfig["OBIS.%d" % (i+1)][ds[i]] + " "
                else:
                    rv = rv + ds[i] + " "
            i+=1
            
    return rv
            
#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main() :

  #config.doNotParseCommandline = True  
  
  with config.configClass() as configuration:
    globals.config= configuration
    
    auth=bytes(bytearray.fromhex(globals.config.configMap["COSEM"]["AUTH"]))
    enc=bytes(bytearray.fromhex(globals.config.configMap["COSEM"]["ENC"]))
    
    print ("keys are %s %s " %(str(enc), str(auth)))

    OBISconfig = configparser.ConfigParser()
    OBISconfig.read('/etc/obis.ini')
    ser = "ttyUSB.irKopf"
    foo = cosem(ser)
    
    encOldData=[]
    encOldData.extend(range(0,400))
    
    while True:
        a=foo.timedQuery()
        #a=b'\x7e\xa0\x76\xce\xff\x03\x13\x3c\x02\xe6\xe7\x00\xdb\x08\x4c\x47\x5a\x67\x72\xaa\x06\xb6\x5e\x30\x00\x03\xc1\xa5\xff\xd3\x05\xd0\x59\x05\xfd\xb6\xfc\xe8\x31\x78\xa1\x12\x30\x00\xe1\x9e\x99\x97\x3d\x62\x0e\xbf\x4f\x60\x5d\x8d\xb5\x6f\x9c\xd9\x06\xa7\x50\x99\xf3\x8a\x2b\x3c\x8d\x51\x62\x26\x14\x21\xf6\x15\xa0\x92\x76\x45\xa9\xc2\xa8\x69\xd0\x2e\xeb\x04\x84\x8c\x3e\x4c\x3e\xa3\x82\x31\xf5\xb5\x3d\xcd\xa2\xce\x60\x96\x90\xf1\x05\x77\xf0\xc7\x9e\x06\xf6\xca\x8e\xc9\x06\xfb\x47\x7e'
        foo.printHex(a, olddata)
        x = dict()
        
        x=foo.parse(x, a, pattern)
        if (0 == foo.plausibilityCheck(a, x)):        
            if "encrypted" in x:
                foo.gcmAESdecrypt(x, enc, auth) # returns empty array if not authenticated
                if "decrypted" in x:
                    data = x["decrypted"][0]
                    print("data is %s " % str(data))
                    
                    foo.printHex(data, encOldData)
                    #decode decrypted data
                    if len(data) > 0:
                        x=foo.parse(x,data,decryptedPattern)
                    
                
        
        #if olddataParsed[i]!=t:
        #    s+=bcolors.FAIL + str(t) + bcolors.ENDC
        #else:
        #    s+=t + ""
        #    
        #olddataParsed[i]=t
        #debugging :
        #t = "%s%s%s " %(pattern[i][1], t, pattern[i][2])
            
        
        print("") # empty line
        #print ("parse returned: %s" % str(x))
        #xx = collections.OrderedDict(sorted(x.keys()))
        xx = x.keys()
        for key in xx:
            print ("%50s %s %s" % (key, str(x[key][0]), x[key][1]))
        
        
        print("") # some empty lines
        print("") # some empty lines
        print("--------------------------------------------------------------------------------------------") # some empty lines
         
        #break
       

if __name__ == '__main__':
  main()

