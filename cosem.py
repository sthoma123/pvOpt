#!/usr/bin/python3
# OBSOLETE; use cosemDecode.py

##

#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
print ("imported " + __name__)

import serial, time

import struct

try:
    #from Crypto.Cipher import AES
    from Cryptodome.Cipher import AES
except:
    print ("Cryptodome not installed")
    pass

import binascii

import globals
import config
import collections
import configparser
import logging
import dpLogger


#---------------------------------------------------------------
def printError(s):
    return print (bcolors.FAIL + str(s) + bcolors.ENDC)
    

def unused4 (by):
    return unused(by, 4)

def unused2 (by):
    return unused(by, 2)

def unused1 (by):
    return unused(by, 1)

def unused (by, n):
    return n, ''.join('{:02x}'.format(x) for x in by[0:n])
    
def hex1str(by):
    return 1, '{:02x}'.format(by[0])
    
def int1(by):
    return 1, intN(by,1)
    
def hex2str(by):
    return 2, hexNstr(by,2)

def hex3str(by):
    return 3, hexNstr(by,3)

def hex4str(by):
    return 4, hexNstr(by,4)
    
def hex5str(by):
    return 5, hexNstr(by,5)
    
def hex11str(by):
    return 11, hexNstr(by,11)

def hex12str(by):
    return 12, hexNstr(by,12)

def str2str(by):
    try:
        s=by[0:16].decode('utf-8')
    except Exception as e:
        printError ("str2str got error %s" % str(e))
        s="unknown"
       
    return 16, s


def str3str(by):
    return 3, strNstr(by, 3)
    
def str5str(by):
    return 5, strNstr(by, 5)
    #try:
    #    s=by[0:5].decode('utf-8')
    #except Exception as e:
    #    printError ("str2str got error %s" % str(e))
    #    s="unknown"       
    #return 5, s
    
def strNstr(by, num):    
    try:
        s=by[0:num].decode('utf-8')
    except Exception as e:
        printError ("str%dstr got error %s" % (num,str(e)))
        s="unknown"       
    return s

def hexNstr(by, num):
    s=""
    for j in range(0,num):
        s += '{:02x} '.format(by[j])
    return s

def intN(by, num):
    i=0
    for j in range(0,num):
        i=256*i+by[j]
    return i

def int4str(by):
    return 4, "%08d"%intN(by,4)

def int2str(by):
    return 2, "%04d"%intN(by,2)

def int1str(by):
    return 1, "%02d"%intN(by,1)

def float4str(by):
    return 4, "%f" % struct.unpack('f', by[0:4])

def float8str(by):
    return 8, "%f" % struct.unpack('d', by[0:8])
    
def rFloat4(self,by):
    return float4str(reverse(by,4))

def reverse(by, n):
    rv = bytearray(by[0:n])
    rv.reverse
    return bytes(rv)

def binAES(by):
    # here comes the AES decryption.
    # len of bby should be 1 more than the AES part (stop-byte), currently fixed 92 bytes...
    # or 77 or 79
    l = len(by) -15
    if l != 77:
        printError ("AES Framelength is %d; expected %d" % (l, 77))

    print("AES got len: %d, %s" % (l, str(by[0:l])))

    return l, by[0:l]
    
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
def weekday(by):
    i = int(by[0])
    if i > 7 or i < 1:
        printError ("Warning: wrong weekday index %d" % i)
        return 1, ""
    else:
        return 1, weekdayDict[i]
    
def month(by):
    i = int(by[0])
    if i > 12 or i < 1:
        printError ("Warning: wrong monthindex index %d" % i)
        return 1, ""
    else:
        return 1, monthDict[int(by[0])]
    
def hms(by):
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

pattern=[]
for i in range(0, 200):
    pattern.append([hex1str, "", " "])
    
pattern[0]=[hex1str, "start", " "]          # 7E Start
#HDLC header
pattern[1]=[hex1str, "HDLCframeType", " "]          # A0 HDLC FrameType 3 + 3 bits length
pattern[2]=[int1, "length", " "]          #76 lenght
pattern[3]=[hex2str, "destinationAddr", " "]          #CE FF destaddr
pattern[5]=[hex1str, "sourceAddr", " "]          # 03 sourceAddr
pattern[6]=[hex1str, "controlField", " "]          # 13 controlfield
pattern[7]=[hex2str, "headerControlSequence", " "]          # 3C 02 control sequence calculated over header

#LLC header
pattern[9]=[hex3str, "LLC frame header", " "] # E6 E7 00 LLC frame header OK!!!

pattern[12]=[hex2str, "UNK2", " "] # DB 08 unknown

#start System Title
pattern[14]=[str3str, "systemTitle", " "] # in ascii, printeable --> "LGZ" 
pattern[17]=[hex5str, "systemTitleSerialNumber", " "] # serial number of LGZ

#
pattern[22]=[int1, "lengthRemaining", " "] # length of remaining bytes 94
pattern[23]=[hex1str, "securityByte", " "]          # 30 means encryption & authentication used here
pattern[24]=[hex4str, "sequence", " "]          # sequence used as nonce.
#----start AES encryption: starts at 27, len:120-27-1=92
pattern[28]=[binAES, "AESframe", "-"] #aes frame
pattern[105]=[hex12str, "AuthTag", "-"] #Authentication TAG


pattern[119]=[hex1str, "stop", " "] #stop


#pattern[17]=[int2str, "year", "-"] #year #07 E0 0B 08 02 0E 05 28 00 80 00 00 Datum Uhrzeit
#pattern[19]=[month, "mont", "-"] #mont
#pattern[20]=[int1str, "day", " "] #day
#pattern[21]=[weekday, "", " "] #weekday
#pattern[22]=[int1str, "hour", " "] #h:m:s
#pattern[23]=[int1str, "min", " "] #h:m:s
#pattern[25]=[unused4, "un1", ") "] #millisec, 2bytes TZ offset, clockstate
#pattern[29]=[hex2str, "", " "]    # 02 07 
#pattern[24]=[int1str, "sec", " "] #h:m:s
#pattern[31]=[hex2str, "", " "]    # 09 10 
#pattern[33]=[str2str, "COSEM Logical number", " "] #serial number 16 byte
#pattern[119]=[hex1str, "stop", " "] #stop
#

#pattern[13]=[int4str, "seq", " "] #sequence
#pattern[18]=[int2str, "year", "-"] #year
#pattern[20]=[month, "mont", "-"] #mont
#pattern[21]=[int1str, "day", " "] #day
#pattern[22]=[weekday, "", " "] #weekday
#pattern[23]=[int1str, "hour", " "] #h:m:s
#pattern[24]=[int1str, "min", " "] #h:m:s
#pattern[25]=[int1str, "sec", " "] #h:m:s
#pattern[26]=[unused4, "un1", ") "] #millisec, 2bytes TZ offset, clockstate


#pattern[30]=[unused2, "un2", ") "] #
#pattern[32]=[unused1, "un3", ") "] #
#pattern[33]=[int2str, "32.7.0", "V "] # Spannung L1
#pattern[35]=[unused1, "un4", ") "] #
#pattern[36]=[int2str, "52.7.0", "V "] # Spannung L2
#pattern[38]=[unused1, "un5", ") "] #
#pattern[39]=[int2str, "72.7.0", "V "] # # Spannung L2
#pattern[41]=[unused1, "un6", ") "] #
#pattern[42]=[int2str, "31.7.0", "A "] # # 
#pattern[44]=[unused1, "un7", ") "] #
#pattern[45]=[int2str, "51.7.0", "A "] # # 
#pattern[47]=[unused1, "un8", ") "] #
#pattern[48]=[int2str, "71.7.0", "A "] # # 
#pattern[50]=[unused1, "un9", ") "] #
#pattern[51]=[int4str, "1.7.0", "W "] # wirkleistung bezug momentan
#pattern[55]=[unused1, "un10", ") "] #
#pattern[56]=[int4str, "2.7.0", "W "] # wirkleistung einsp momentan
#pattern[60]=[unused1, "un11", ") "] #
#pattern[61]=[int4str, "1.8.0", "kWh "] #
#pattern[65]=[unused1, "un12", ") "] #
#pattern[66]=[int4str, "2.8.0", "kWh "] #
#pattern[70]=[unused1, "un13", ") "] #
#pattern[71]=[int2str, "?1=", "? "] # # 
#pattern[73]=[unused1, "un14", ") "] #
#pattern[74]=[int2str, "?2=", "? "] # # 
#pattern[76]=[unused1, "un15", ") "] #
#pattern[77]=[int2str, "?3=", "? "] # # 
#pattern[91]=[hex1str, "stop", " "] #sequence
#pattern[79]=[unused2, "un16", ") "] #
#
#pattern[81]=[str2str, "ID", " "] #serial number
#pattern[89]=[int2str, "CRC", " "] #

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
        l,t=hex1str(by)
        s += t
        i += l

    return s


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class cosemException(Exception):
    errId=0
    reason=""
    def __init__(self, errId, reason):
        self.reason = reason
        self.errId = errId
    def __str__(self):
        return "cosemException ID is %s, %s" % (repr(self.errId), repr(self.reason))

class cosem(object):

    def AESdecrypt(self, data, key, auth):  #data as dictionary key and auth as bytes

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
        iv = bytes(data["systemTitle"][0],"utf-8")                     #3
        iv += toBin(data["systemTitleSerialNumber"][0])       #5
        iv += toBin(data["sequence"][0])          #4  -> 12
        
        #• autentication tag (T) – 12 bytes
        tag = toBin(data["AuthTag"][0])           #12
        #tag += binascii.unhexlify(data["stop"][0].replace(" ", ""))             #1 -> 12
        
        #• additional auth. data (AAD = security-byte+auth key) – 17 bytes
        addAuthData = toBin(data["securityByte"][0])     #1
        addAuthData += auth                                    #16-> 17
        
        #• encryption key (EK) – 16 bytes
        ek = key
        
        # ciphertext (C) – 77 bytes (79, 92)
        by = data["AESframe"][0]
        nonce = toBin(data["sequence"][0])  # 4 bytes

        print("key  = %s" % (self.sprintHex(ek,old[0])))
        print("auth = %s" % (self.sprintHex(auth,old[1])))
        print("iv   = %s" % (self.sprintHex(iv,old[6])))
        print("nonce= %s" % (self.sprintHex(nonce,old[2])))
        print("tag  = %s" % (self.sprintHex(tag,old[3])))
        print("AADat= %s" % (self.sprintHex(addAuthData,old[4])))
        print("data = %s" % (self.sprintHex(by,old[5])))
        
        cipher = AES.new(ek, AES.MODE_GCM, nonce) #, mac_len=16)
        cipher.nonce = nonce
        rv = ""
        try:
            #rv = cipher.decrypt_and_verify(by, tag)
            rv = cipher.decrypt(by)
            print("decrypted = %s " % self.sprintHex(rv, oldDataDecrypt))
            cipher.verify(tag)                    
            print ("verification Ok.")
            
        except Exception as e:
            printError ("verify got exception %s" % str(e))
            
        #print("decrypted = %s " % self.sprintHex(rv, oldDataDecrypt))
       
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
        
        
    def __init__(self, serial_port = "ttyUSB.irKopf"):
        
        self.ser = serial.Serial(
            port = "/dev/" + serial_port,
            baudrate = 9600,
            bytesize = serial.EIGHTBITS,
            parity = serial.PARITY_NONE,
            timeout = 3.0) #actually timeot is max 1.5s between chars and 2.2s after id message

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
        
    def query(self):
        #oldstate=77
        x = b''
        x = self.ser.read(92)  #seems to be bytearray always 92 bytes
        if len(x) == 0 :
            raise cosemException(cosemExTimeout, 
                "QueryError: timeout while reading")
                
        return x
        
#-----------------------------------------------------------------------------------------------------------
    def timedQuery(self):
        rv = bytearray(b'')
        while True:
            x = self.ser.read(1)
            if 0 == len(x): #timeout (1 sec)
                break
            else:
                rv.append(x[0])
                
        return rv

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
            l,t=hex1str(by)

            t = "%s " %(t)
            if olddata[i]!=t:
                s+=bcolors.FAIL + t + bcolors.ENDC
            else:
                s+=t + ""
            olddata[i]=t

            i+=l               
            
        s = "(%s) %s" % (len(cont),s)
        
        return s
    

#-----------------------------------------------------------------------------------------------------------
# obsolete:
#-------------
    def _tryQuery(self):
        # macht query mit retries abhyengig vom errorcode
        a=None
        rv = None
        retry=10
        while retry > 0 and rv is None:
            lastErr=cosemException(0,"")
            try:
                a = self.query()
                #rv = self.parse(a)
            except cosemException as e:
                print ("cosem try got error %s" % str(e))
                lastErr=e
                
            self.setSerBaudrate("5") # back to 9600 baud
            self.checkIfIdle()

            retry -= 1


        return rv
    
        
#-----------------------------------------------------------------------------------------------------------
    def parse(self, cont, pattern):
        rv = dict()
        frameLen = len(cont) # should match length bytes
        global olddataParsed

        
        i=0
        s=""
        
        while i<len(cont):
            l,t=pattern[i][0](cont[i:]) #call decoding function depending on byte index.
            rv[pattern[i][1]]= [t,  pattern[i][2]]  #[1] is what [2] is unit

            t = "%s%s%s" %(pattern[i][1], t, pattern[i][2])
            if olddataParsed[i]!=t:
                s+=bcolors.FAIL + str(t) + bcolors.ENDC
            else:
                s+=t + ""
            olddataParsed[i]=t
            i+=l
               
               
        print ("%s" % (s))
        #print ("rv = %s" % (str(rv)))

        #some plausibility checks:
        if "start" not in rv:
            printError ("ParseError no frame start byte: Frame should start with 0x7e")
        else:
            if rv["start"][0] != '7e':
                printError("ParseError wrong frame start byte (%s instead of 7e)" % rv["start"][0])
                #   raise cosemException(cosemWrongStart, "ParseError wrong frame start byte (%s instead of 7e)" % rv["start"])
            else:   
                print ("ParseOk: Starte Bytes Ok: %s" % str(rv["start"][0]))


            
        if "stop" not in rv:
            printError("ParseError no frame stop byte: Frame should stop with 0x7e")
            #raise cosemException(cosemNoStop, "ParseError no frame stop byte")
        else:
            if rv["stop"][0] != '7e':
                printError ("ParseError wrong frame stop byte (%s instead of 7e)" % rv["stop"])
                #raise cosemException(cosemWrongStop, 
                #    "ParseError wrong frame stop byte (%s instead of 7e)" % rv["stop"])
            else:
                print ("ParseOk: Stop Byte Ok: %s" % str(rv["stop"][0]))
        
        if "length" not in rv:
            printError("ParseError no length field in frame")
            #raise cosemException(cosemNoStop, "ParseError no frame stop byte")
        else:
            if rv["length"][0]!= frameLen - 2:
                printError ("ParseError: FrameLen does not match length in frame header %s != (%s - 2)" % (str(rv["length"][0]), str(frameLen)))
            else:
                print ("ParseOk: length in Header is Ok: %s" % str(rv["length"][0]))
            
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
            
import configparser

#----------------------------------------------------------------------------------------------------
def cli():
    """Start the command line interface."""
    parser = argparse.ArgumentParser(
        description="reads homematic ccu, give homematic datapoint nn the form "
                    "  address/channel/property ")
    parser.add_argument("-d", "--dp", metavar='Datapoint',
                        type=str, default = "/",  #NEQ1489656/4/ACTUAL_TEMPERATURE
                        help="datapoint in the form address/channel/property")
                        
    parser.add_argument("-c", "--ccu", 
                        type=str, default = "HMRASPI",
                        help="CCU servername")

    parser.add_argument("-v", "--value", 
                        type=str, default = "",
                        help="value")

    parser.add_argument("-p", "--pulse", 
                        type=str, default = 0,
                        help="pulsetime in seconds")

    args = parser.parse_args()

    if all(arg in (False, None) for arg in (
            args.dp, args.ccu)):
        parser.print_help()
    
    return (args.ccu, args.dp, args.value, args.pulse)


#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main() :

  config.doNotParseCommandline = True  
  #hmAddress, dp, value, pulse = cli()
  
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
        #a=foo.tryQuery()
        a=foo.timedQuery()
        foo.printHex(a, olddata)
        
        x=foo.parse(a, pattern)
        if "AESframe" in x:
            data=foo.AESdecrypt(x, enc, auth) # value/unit-pair
            print("decrypted data is %s " % (str(data)))
            foo.printHex(data, encOldData)
            
        
        print("") # empty line
        #print ("parse returned: %s" % str(x))
        #xx = collections.OrderedDict(sorted(x.keys()))
        xx = x.keys()
        for key in xx:
            print ("%50s %s %s" % (key, str(x[key][0]), x[key][1]))
        
                
        print("") # some empty lines
        print("") # some empty lines
        print("--------------------------------------------------------------------------------------------") # some empty lines
        


if __name__ == '__main__':
  main()

