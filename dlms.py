#!/usr/bin/python3

import serial, time

import collections
import configparser


ACK = b'\x06'
NAK = b'\x15'
STX = b'\x02'
ETX = b'\x03'

dlmsExTimeout   =1
dlmsExIllIdent  =2
dlmsNoLF        =3
dlmsNoSTX       =4
dlmsChecksum    =5
dlmsNAK         =6
dlmsIDTooShort  =7
dlmsLast        =8
	
def myParser(s):
    def parseHelper(level=0):
        rv = [""]
        while 1:
            try:
                token = next(tokens)                
            except StopIteration:
                if level != 0:
                    raise Exception('missing closing paren')
                else:
                    return rv
            if token == '*':  #split on same level (unit separator)
                rv.extend([""])
            elif token == '&':  #split on same level (some other indicator)
                rv.extend(["&"])                
            elif token == ')':
                if level == 0:
                    raise Exception('missing opening paren')
                else:
                    return [rv]
            elif token == '(':
                rv.extend(parseHelper(level+1))
            else:
                rv[-1] = rv[-1] + token
                #return [token] + parseHelper(level)
    tokens = iter(s)
    return parseHelper()

class dlmsException(Exception):
    errId=0
    reason=""
    def __init__(self, errId, reason):
        self.reason = reason
        self.errId = errId
    def __str__(self):
        return "slmsException ID is %s, %s" % (repr(self.errId), repr(self.reason))

class dlms(object):
    def speedFromChar(self, speed):
        new_baud_rate = 300  # default
        if (speed == "1"): new_baud_rate = 600
        elif (speed == "2"): new_baud_rate = 1200
        elif (speed == "3"): new_baud_rate = 2400
        elif (speed == "4"): new_baud_rate = 4800
        elif (speed == "5"): new_baud_rate = 9600
        elif (speed == "6"): new_baud_rate = 19200
        return new_baud_rate

    def sendSpeedMsg(self, speedChar):
        changeSpeedMsg= ACK + b'0' + bytes(speedChar,"utf-8") + b'0\r\n' # IEC 62056-21:2002(E) 6.3.3        
        #print("write speed changemsg %s" % str(changeSpeedMsg))        
        time.sleep(0.2) # wait until meter accepts commands
        self.ser.write(changeSpeedMsg)
        time.sleep(0.2) # wait until data is transmitted
        
    def setSerBaudrate(self, speedChar):
        newBaudrate=self.speedFromChar(speedChar)
        #print ("Change to %d baud" % newBaudrate)
        self.ser.baudrate=newBaudrate

    def changeSerSpeed(self, speedChar):    
        return 0
        
        #first: send speed-change command with old speed (don't know 
        self.sendSpeedMsg(speedChar)
        #second: change serial comport speed.
        self.setSerBaudrate(speedChar)
        return 0
        
        
    def __init__(self, serial_port = "ttyUSB1"):
        
        self.ser = serial.Serial(
            port = "/dev/" + serial_port,
            baudrate = 300,
            bytesize = serial.SEVENBITS,
            parity = serial.PARITY_EVEN,
            timeout = 3.0) #actually timeot is max 1.5s between chars and 2.2s after id message

    def close(self):
    
        self.ser.close()
            
    def checkIfIdle(self, tox = 3.5):
        timSaf=self.ser.timeout
        self.ser.timeout = tox
        x=b'x'
        buf = ""
        print ("Waiting for silence")
        while True:            
            x = self.ser.read(1)
            if len(x) == 0:
                break
        
            if x[0]>31:
                buf += x.decode('utf-8')
                
            if x[0] == 10: # log every line
                print("%s" % buf)
                buf=""                    
        

        self.ser.timeout = timSaf
        return (0)
        
    
    def query(self):
        self.ser.write((bytes("/?!\r\n","UTF8")))
        state = 0
        id = ""
        cont = ""
        buf = ""
        sum = 0
        #oldstate=77
        
        while True:
            x = self.ser.read(1)  #seems to be bytearray

            #if state != oldstate:
            #    print ("state is ", state)
            #    oldstate = state
                
            
            if len(x) == 0:
                raise dlmsException(dlmsExTimeout, "Rx Timeout")
            #b = bytearray(a,"UTF8")[0]
            
            b = x[0]
            a = x.decode('utf-8') # make it a string!
            #print (a)

            if state == 0:
                # Read ID string 
                if b >= 32:
                    id += a
                elif b == 13:
                    state = 1
                    #print ("id is <<%s>>" % id)
                elif b == 21:
                    raise dlmsException(dlmsNAK, 
                        "got NAK 0x%02x, expected ident " % b)
                    state = 99
                else:
                    raise dlmsException(dlmsExIllIdent, 
                        "Illegal char in ident 0x%02x" % b)
                    state = 99
            elif state == 1:
                # NL ending ID string
                if b != 10:
                    raise dlmsException(dlmsNoLF,
                        "Expect LF after CR, got 0x%02x" % b)
                    state = 99
                else:
                    if len(id)>4:
                        speedChar=id[4]
                        self.changeSerSpeed(speedChar)
                        state = 2
                    else: 
                        raise dlmsException(dlmsIDTooShort,
                            "ident too short, %s" % id)                            
                        state = 99
            elif state == 2:
                # STX
                if b != 2:
                    raise dlmsException(dlmsNoSTX,
                        "After speed change: Expected STX not 0x%02x" % b)
                    state = 99
                else:
                    state = 3
            elif state == 3:
                # message body
                sum ^= b
                if b != 3:
                    cont += a
                    buf += a
                    if b == 10: # log every line
                        #print("got <<%s>>" % buf)
                        buf=""                    
                else:
                    state = 4
            elif state == 4:
                # Checksum
                if sum != b:
                    print ("IGNORED: Warning: checksum do not match 0x%02x != 0x%02x " % (sum, b))
                    return self.parse(id, cont)
    
                    #raise dlmsException(dlmsChecksum, 
                    #    "Checksum Mismatch")
                    #state == 99
                else:
                    return self.parse(id, cont)
                    
            elif state == 99:
                # Error, flush
                print ("error - waiting for cleanup")
                #aufraeumen
                self.setSerBaudrate("0")
                pass
        assert False

    def tryQuery(self):
        # macht query mit retries abhyengig vom errorcode
        a=None
        retry=10
        while retry > 0:
            lastErr=dlmsException(0,"")
            try:
                a = self.query()
            except dlmsException as e:
                print ("try got %s" % str(e))
                lastErr=e
            
            if lastErr.errId == 0:
                break
                
            if lastErr.errId == dlmsExTimeout:
                print ("got no answer with baudrate: %d" % self.ser.baudrate)
                if self.ser.baudrate != 300:
                    self.setSerBaudrate("0") # back to 300 baud
                    print ("try again with: %d" % self.ser.baudrate)
                else:
                    #macht es sinn, 10x mit 300 zu probieren? ev. gleich ein break machen
                    pass
                
            elif lastErr.errId == dlmsExIllIdent: 
                # offenbar brabbelt der zaehler noch irgendwas 
                print ("Zaehler brabbelt noch")
                self.setSerBaudrate("0") # back to 300 baud
                self.checkIfIdle()
                #    print("Warte 3sec")
                #    time.sleep(3)
                #else:
                #    print("Warte 0.5 sec")
                #if self.ser.baudrate==300: # that could take longer...
                #    time.sleep(0.5) # wenn er noch etwas mit 19.200 sagt, dann geht's schneller
            else:
                # some other protocol error. probably different target?
                print ("got error %s retry %d" % (str(lastErr), retry))
                self.setSerBaudrate("0") # back to 300 baud
                self.checkIfIdle()
                            
            retry -= 1
                
        
        if lastErr.errId == 0:    
            return a
        else:
            return None
    
        
    def parse(self, id, cont):
        #l = list()
        #l.append(id)
        #l.append(dict())
        l = dict()
        l["ID"]=[id]
        cont = cont.split("\r\n")
        if cont[-1] != "":
            raise dlmsException(dlmsLast, 
                "ParseError Last data item lacks CRNL")
        if cont[-2] != "!":
            raise dlmsException(dlmsLast,
                "ParseError Last data item not '!'")
        for a in cont[:-2]:
            if a[-1] != ")":
                raise dlmsException(dlmsLast,
                    "ParseError Last char of data item %s not ')'" % a)
                return None
            #1.8.5(0.000*kWh)
            #value/unit pairs are enclosed in parenthesis ()
            #unit is delimited by asterisk *
            #can be more than 1 value/unit pairs.

            b = myParser(a)
            #a = a[:-1].split("(")
            #b = a[1].split("*")
            #strings on first level is key
            key = ""
            data=list()
            for item in b:
                if type(item) is str:
                    key = key + item + "-" 
                else:
                    #data = data + item
                    data.extend(item)
                    
            if key[-1] == "-":
                key=key[:-1]
                
            l[key] = data
            #l[b[0]] = b[1:]
        return l
            

def OBISTranslate(aData, OBISconfig):
    rv=""    
    #print (aData)
    if aData in OBISconfig["OBIS"]: # found direct translation
        rv = OBISconfig["OBIS"][aData]
    else:
        ds=aData.split(".")
        #print ("ds is ")
        #print (ds)
        i=0
        while i < 3:
            if len(ds)>i:
                #print ("ds[i] is " + str(ds[i]))
                #print (list(OBISconfig.keys()))
                #print ("obiskey is OBIS.%d" % (i+1))
                #print (OBISconfig["OBIS.%d" % (i+1)])
                
                if ds[i] in OBISconfig["OBIS.%d" % (i+1)]:
                    rv = rv + OBISconfig["OBIS.%d" % (i+1)][ds[i]] + " "
                else:
                    rv = rv + ds[i] + " "
            i+=1
            
    #print ("%s maps to %s" % (aData, rv))
    return rv
            
import configparser

if __name__ == "__main__":
  OBISconfig = configparser.ConfigParser()
  OBISconfig.read('/etc/obis.ini')

  ser = "ttyUSB0"
  foo = dlms(ser)
  while True:
    a=foo.tryQuery()
    
    if a is None:
        print ("No Connection to %s " % ser)
    else:
        #b=translateOBIS(OBISconfig,a[1])
        #a ist dict  dict mit liste von daten. Daten sind Liste, zweites Element ist meist Einheit
        #print("%16s: %s" % ("identifier", a[0]))
        #print("")
        aa=collections.OrderedDict(sorted(a.items()))
        for key in aa:
            dat = a[key]
            desc = OBISTranslate(key, OBISconfig)
            #print (str(key), str(dat), str(desc))
            d1=dat[0]
            d2=""
            if len(dat)>1:
                d2=dat[1]
                #if key=="1.8.0" or key=="2.8.0" or key == "1.7.0" or key == "2.7.0":
            print ("%50s (%7s) %s %s" % (desc, key, d1, d2))
            
            
            
            #if len(j) == 2:
            #    pass
            #    print("%10s %10s [%5s] - %s" % (key, j[0], j[1], iDesc))
            #else:
            #    pass
            #    print("%10s: %10s        - %s" % (key, j[0], iDesc))
            
        diff=  float(a["1.7.0"][0]) -  float(a["2.7.0"][0])            
        print ("Ent: ", a["1.7.0"], "Ein: ", a["2.7.0"], "bilanz: ", [diff, a["1.7.0"][1]])
        
        #time.sleep(3.0) # wait until data is transmitted
