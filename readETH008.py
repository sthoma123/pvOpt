#!/usr/bin/python3
import os, glob, time,  sys, datetime
import select
import struct
import socket    # used for TCP/IP communication
import globals
import config
import logging
import cache
import metadata
from funcLog import logged
import socketserver

import queue
import threading
import eventhandler


#Command for ETH008:
#Action
#hex command
#10     Get Module Info, returns 3 bytes. Module Id (19 for ETH008), Hardware version, Firmware version.
#20     Digital active - follow with 1-8 to set relay on, then a time for pulsed output from 1-255 (100ms resolution) or 0 for permanent 
#Board will return 0 for success, 1 for failure 
#21     Digital inactive - follow with 1-8 to turn relay off, then a time for pulsed output from 1-255 (100ms resolution) or 0 for permanent 
#Board will return 0 for success, 1 for failure 
#23     Digital set outputs - the next single byte will set all relays states, All on = 255 (11111111) All off = 0
#Board will return 0 for success, 1 for failure 
#24     Digital get outputs - sends a single byte back to the controller, bit high meaning the corresponding relay is powered
#32     Get Analogue Voltage - follow with 1-8 for channel and ETH8020 will respond with 2 bytes to form an 16-bit integer (high byte first)
#3A     ASCII text commands (V4+) - allows a text string to switch outputs, see section below
#77     Get serial number - Returns the unique 6 byte MAC address of the module.
#78     Get Volts - returns relay supply voltage as byte, 125 being 12.5V DC
#79     Password entry - see TCP/IP password
#7A     Get unlock time - see section below 
#7B     Log out - immediately re-enables TCP/IP password protection

#command for 2428
# 0x30 Get Status
# 0x31 Set relay
# 0x32 Set output
# 0x33 Get Relays (first byte is selected relay, subsequent bytes are all relays)
# 0x34 Get Inputs
# 0x35 Get Analogue
 
# Prepare 3-byte control message for transmission
 



#----------------------------------------------------------------------------------------------------
# warning: message must be bytes!!! bytes are e.g. message=bytes([12, 13, 14])
@logged(logging.DEBUG)
def io_relais_raw(box, message, timeout=0): #network name of device
    TCP_PORT = 17494
    #TCP_PORT = 17123
    BUFFER_SIZE = 80
    try:
        if timeout == 0:
            timeout = 60000  # wait a minute for the board.
        
        # Open socket, send message, close socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((box, TCP_PORT))
        
        hexString=":".join("{:02x}".format(c) for c in message)
        logging.debug("io_relais_raw sends string: %s to %s" % (hexString, box))
        
        #s.send(bytes(message,"UTF8"))
        s.send(message)
        
        s.setblocking(0)
        ready = select.select([s], [], [], timeout/1000)
        if ready[0]:
            cont = s.recv(BUFFER_SIZE)
        else:
            cont = list()
            hexString=":".join("{:02x}".format(c) for c in message)
            logging.error("io_relais_raw: box %s did not answer anything after %d ms on command 0x%s" % (box, timeout, hexString))
            #print("io_relais_raw: box %s did not answer anything after %d ms on command 0x%s" % (box, timeout, hexString))

        hexString=":".join("{:02x}".format(c) for c in cont)  # ord(c)
        #print ("io_relais_raw receives string: %s" % hexString)

        s.close()
    except socket.error as e:
        logging.exception("unable to read %s " % box)
        cont = None
        
    return cont

#----------------------------------------------------------------------------------------------------
# returns 0 for "old" binary command type board
# returns 1 for "new" board like the 2824 dscript board (it has different binary commands.
#
@logged(logging.DEBUG)
def getBoardType_raw(typeBox):

    box = typeBox[4:]
    rv = 0
    statusRequest = bytes([0x10,]) #'\ get ETH008 and ETH8020 (2824 will fall into timeout)
    #get Module Info - returns 3 bytes. Module Id (19 for ETH008), (21 for ETH8020), Hardware version, Firmware version.
    #statusRequest = bytes([0x77,]) #'\ get status for 2824
    #statusRequest = bytes([0x32, 0x01]) #'\ get status for 2824
        
    status=io_relais_raw(box, statusRequest, 500)
    if not status is None:
        try:
            if len(status) == 0: #new board returned nothing (tiemout!)
                rv = 1
        except Exception: # ignore error (board returned nothing...)
            pass
    
    return rv

#----------------------------------------------------------------------------------------------------
def getBoardType(box):
    rv = globals.ethcache.get("TYPE" + box, getBoardType_raw, 10*60) # damit nicht der statuscache gelesen wird.
    return rv
    
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read_relais_raw(box): #network name of device

    boardType = getBoardType(box)
    
    if boardType == 0: #old board
        message = bytes([0x24, 0x00, 0x00]) #'\x24\x00\x00' # read Relays 
    else:
        message = bytes([0x33, 0x00]) # new board read relais
    

    rv=io_relais_raw(box, message)
    if not rv is None:            
        rv1=0
        if type(rv) is bytes:
            if boardType == 0: #old board
                rv = reversed(rv)
            for b in rv:
                rv1 = rv1*256+b   #HIER IST EIN PROBLEM!!!
            rv=rv1
        else:
            rv=ord(rv)

    #print ("board read_raw returned " + str(rv))
            
    return rv


#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def io_read_box_int_raw(box, message):

    rv=io_relais_raw(box, message)
    rv1=0
    if not rv is None:            
        rv1=0
        if type(rv) is bytes:
            for b in rv:
                rv1 = rv1*256+b
            rv=rv1
        else:
            rv=ord(rv)
            
    return rv
    
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read_voltage_raw(box): #network name of device

    boardType = getBoardType(box)    
    rv = 0
    if boardType == 0: #old board
        message = bytes([0x78, 0x00, 0x00]) #'\x78\x00\x00' # read Voltage
        rv=io_read_box_int_raw(box, message)
    else:
        message = bytes([0x30, 0x00, 0x00]) #'\x78\x00\x00' # read Status
        rv=io_relais_raw(box, message)
        #print ("returns ", type(rv))
        if not rv is None:            
            if type(rv) is bytes:
                if len(rv) > 5: 
                    rv = rv[5]

        
    return rv/10
    
#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read_analog_raw (box, inputNr):

    boardType = getBoardType(box)    
    rv = 0
    if boardType == 0: #old board
        message = bytes([0x32, inputNr, 0x00]) #'\x78\xchannel\x00' # read Analog
        rv = io_read_box_int_raw(box, message)
    else:
        message = bytes([0x35, inputNr, 0x00]) #'\x78\xchannel\x00' # read Analog
        rv=io_relais_raw(box, message)
        #print ("returns ", type(rv))
        if not rv is None:            
            if type(rv) is bytes:
                i=inputNr*2
                if len(rv) > (i): 
                    rv = rv[i]*256 + rv[i+1]    
                    
    return rv


#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read_relais(box): #network name of device

    rv = globals.ethcache.get(box, read_relais_raw)
    return rv

#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def read1relais(box, number): #network name of device

    rv = None
    x=globals.ethcache.get(box, read_relais_raw)    
    #print ("read1relais readbytes %s " % str(x))        
    
    if x is not None:
        all = [0!=(1<<p)&x for p in range(0,24)]
        if not (len(globals.config.Schalter)<number) :
            s=globals.config.Schalter[number-1]
        else:
            #s="Switch %d" % (number)
            s=""
            
        rv = [ s,  all[number-1] ]
        
    #print ("read1relais returns ", rv)        

    return rv

#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def readVoltage(box):
    
    #nix cachen, da sonst alle bytes der schalter noch im box-cache stehen...
    rv = read_voltage_raw(box)    
    return rv

#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def readAnalog(box, inputNr):

    i = int(inputNr)
    
    rv = read_analog_raw(box, i)
    
    return rv
    
#----------------------------------------------------------------------------------------------------
# expects an integer which is dumped to the relais
#
@logged(logging.DEBUG)
def set_AllRelais (box, state):

#TODO for new box!!!

    message = b'\x23'
    if type(state) is list:
        message += bytes(state)
    else:
        message += bytes([state])    
    
    return io_relais_raw(box, message)

#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def set_relais (box, switch, state, pulse=None):

    if pulse is None:
        pulse = 0
    
    if not type(pulse) is int:
        pulse = 0
        
    boardType = getBoardType(box)    
    rv = 0
    if boardType == 0: #old board
        if state:
          message = b'\x20'
        else:
          message = b'\x21'
        message += bytes([switch]) + bytes([pulse]) ## b"\x00"   #pulsdauer        
    else: # new Board
        #new box: 0x31 ; SR, Set Relay - relay num, state, pulse time/state (4 bytes), total 7 byte command
        message = bytes([0x31]) #'\x24\x00\x00' # read Relays 
        message += bytes([switch])
        message += bytes([state])        
        message += struct.pack(">L", pulse)  #oder >I

    rv = io_relais_raw(box, message)
        
    return rv

#----------------------------------------------------------------------------------------------------
# write:
#    write output to board
#

@logged(logging.DEBUG)
def write(dp, value, pulse=None):

    try:
        
        if type(dp) is str:
            dpList=dp.split('/')
        else:
            dpList=dp

        while len(dpList) < 2:  # brauche zumindest 2 elemente, auch wenn sie leer sind!
            dpList = dpList + [""]
            
        box=dpList[0]        
        globals.ethcache.invalidate(box)   #will change ...

        if dpList[1] == "":     # schreibe ganzes Byte 
            o = set_AllRelais(box,value)        
        else:
            toggle = False
            i=1
            if dpList[i]=="XOR":
                toggle=True
                i=i+1
                switch=int(dpList[i])               
                state = read1relais(box, switch) #network name of device                
                #print ("XOR: state " + str(state))                
                if len(state)>1:
                    value = not(state[1])
                #print ("XOR: value " + str(value))
            switch=int(dpList[i])               
            
            #print ("setting " + box + " switch " + str(switch) + " to " + str(value) + " pulse " + str(pulse))
                
            o = set_relais(box, switch, value, pulse)

        rv = "OK"
    except Exception as e:
        logging.exception ( "writeETH problem with %s" % (dp))
        rv= "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now() , "ETH/%s" %(dp), "Exception"

    return rv

#----------------------------------------------------------------------------------------------------
# getList:
#   gets a plain list of defined variables
#   dp is a part of the datapoint (e.g. the first part of the datapoints
#
@logged(logging.DEBUG)
def getList(dp):
    rv = "to be done"
    return rv
    
#----------------------------------------------------------------------------------------------------
# read:
#   DP=prot/box/ID/SUBID/SUBSUBID
#   box  {ETH:"KELLERSCHALTER"}
#   ID   {ETH: "" | "1-8"}
# returns list: Name, Value, Unit, timestamp

@logged(logging.DEBUG)
def read(dp):

    #print ("readETH008::read " + dp)
    rv = metadata.read("ETH/" + dp)

    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    while len(dpList) < 2:  # brauche zumindest 2 elemente, auch wenn sie leer sind!
        dpList = dpList + [""]
        
    box=dpList[0]
    if dpList[1] == "":     # lese ganzes Byte aus
        o = read_relais(box)
        if o is None:
            rv[5] = "Timeout"
        else:
            rv[1] = o
            rv[3] = datetime.datetime.now()
            rv[5] = "Ok"
    else:
        if dpList[1][0] == "V":  # read voltage
            r=readVoltage(box)
            if r is None:
                rv[5] = "Timeout"
            else:
                rv[1] = r
                rv[3] = datetime.datetime.now()
                rv[5] = "Ok"
        elif dpList[1][0] == "A":  # read analog
            inputNr = 0
            try:
                inputNr=dpList[1][1:]
            except:
                pass
                
            r=readAnalog(box, inputNr)
            if r is None:
                rv[5] = "Timeout"
                rv[3] = datetime.datetime.now()
            else:
                rv[1] = r
                rv[3] = datetime.datetime.now()
                rv[5] = "Ok"
        else:
            i=1
            if dpList[i]=="XOR":  #wird beim Lesen ignoriert.
                i=i+1
            switch = int(dpList[i])
        
            r=read1relais(box, switch)
            
            rv[3] = datetime.datetime.now()
            if r is None:
                rv[5] = "Timeout"
            else:
                rv[1] = r[1]
                if r[0] != "":
                    rv[0] = r[0]
                    
                if rv[0] == "":
                   rv[0]="Switch %d" % (switch)
                   
                #rv =  r + ["", datetime.datetime.now(), "ETH/"+dpList[0]+"/"+str(switch), "Ok"]                    
                rv[5] = "Ok"

    #print ("readETH008::read finished " + dp + " returned " + str(rv))
    
    return rv
    
#----------------------------------------------------------------------------------------------------
def schalteLeinwand():

    dpLeinwand = "ETH/zaehlerschalter/20"
    host="kellerraspi:8000"
    
    prev=driverCommon.readViaWeb(dpLeinwand, 5, host)
    if prev[5]=="Ok":
        stat=prev[1]
        print ("stat: " + str(stat))
        stat = not stat
        
        rv = driverCommon.writeViaWeb(dpLeinwand, stat, host)
    else:
        logging.error("stat of %2 is not Ok (%s)" % (stat, prev[5]))


            
#----------------------------------------------------------------------------------------------------
# handler klasse:
#
class ETHHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
#----------------------------------------------------------------------------------------------------
# gotPasswortCmd:
#
    @logged(logging.DEBUG)
    def gotPasswortCmd(self, password):
        #alle passworter are valid; return 1 (2 wenn falsch)
        #ich koennte dort noch nutzdaten auslesen.
        #
        print ("password = " + str(password))
        
        rv = bytes([1,])
        return rv

#----------------------------------------------------------------------------------------------------
# gotSwitchCmd:
#
#  Reply with a 0 for success, else send 1
#
    @logged(logging.DEBUG)
    def gotSwitchCmd(self, state, switch):

        print ("switch  = " + str(state) + "---" + str(switch))
        
        eventhandler.enqueue(eventhandler.EXTEvent, "ETH/%s/%s" %(str(state), str(switch)), state)
        #if state and (switch == 4): #wohnzimmer unten
        #    schalteLeinwand();
        
        rv = bytes([0x00])
        return rv
    


#----------------------------------------------------------------------------------------------------
# handle:
#
    @logged(logging.DEBUG)
    def handle(self):
        # self.request is the TCP socket connected to the client
        #do not close connection after first received packet
        print("{} communication started:".format(self.client_address[0]))
        while 1:
            self.data = self.request.recv(1024)
            if not self.data:
                break
            
            print("got " + hex(self.data[0]) + "  " + str(self.data ))
            
            rv = bytes([0x02])
            
            if self.data[0] == 0x79:
                rv = self.gotPasswortCmd(self.data[1:])
            elif self.data[0] == 0x20:  #active
                rv = self.gotSwitchCmd(True, int(self.data[1]))
            elif self.data[0] == 0x21:   #inactive
                rv = self.gotSwitchCmd(False, int(self.data[1]))

            print("returning " + hex(rv[0]))
            self.request.send(rv)
        print("{} communication finished:".format(self.client_address[0]))
        print("")
            
#----------------------------------------------------------------------------------------------------
# worker:
# hier werden inputs von eth-boards behandelt:
# ich mache 2 threads, da der socket-server blockiert, und ich ihn ueberwachen bzw. bei 
# einem shutdown sauber runterfahren will.
#
#
#ETHPORT = 17495  #zum testen
ETHPORT = 17494  #richtig

def worker(dummy):
    t = threading.Thread(target=start_ETHserver, args = (ETHPORT, ), name="ETHserver_Worker")
    t.daemon = True
    t.start()
    
    while (not globals.shutdown):
        t.join(8.0)
       
    if "ETHserver" in dir(globals):
        globals.ETHserver.shutdown()
        globals.ETHserver.server_close()
    
    t.join(2.0)
    
    
    
#----------------------------------------------------------------------------------------------------
# server auf port:
def start_ETHserver(port):
    try:
        # Create the server, binding to localhost on port x
        globals.ETHserver = socketserver.TCPServer(("", port), ETHHandler)
        print ("starting ETHserver at port  %d" % (port))

        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        globals.ETHserver.serve_forever()    
            
    except socket.error as e:
        logging.exception("ETHServer: unable to serve port %d; error %s" % (port, str(e)))
        print ("ETHServer: unable to serve port %d; error %s" % (port, str(e)))
        globals.shutdown = True
        globals.restart = True
        
    logging.error("finishing serverthread")
    print ("finishing serverthread")


#----------------------------------------------------------------------------------------------------
# MAIN:
#
def main() :
  with config.configClass() as configuration:
    globals.config= configuration
    #print ("metadata: start - with - debug")
    #logging.getLogger().setLevel(logging.DEBUG)
    if 1:
        dp="Kueche/9"
        print("read %s returns " % dp, read(dp))
        dp="KELLER2/7"
        print("read %s returns " % dp, read(dp))
        print("write %s returns " % dp, write(dp,1))
        print("read %s returns " % dp, read(dp))
        print("write 0 %s returns " % dp, write(dp,0))
        print("read %s returns " % dp, read(dp))
    
    if 0:
        dp="Kueche/9"
        print("read %s returns " % dp, read(dp))
        print("write %s returns " % dp, write(dp,1))
        print("read %s returns " % dp, read(dp))
        print("write 0 %s returns " % dp, write(dp,0))
        print("read %s returns " % dp, read(dp))
        
        dp="keller2/3"
        print("read returns ", read(dp))
        dp="keller2/4"
        print("read returns ", read(dp))
        dp="keller2/5"
        print("read returns ", read(dp))
        dp="Kueche/9"
        print("read returns ", read(dp))
        dp="Wohnzimmer/9"
        print("read returns ", read(dp))
        #sys.exit()
        
    while 0:
        dp="Wohnzimmer/V"
        print("read returns ", read(dp))       
        dp="Kueche/V"
        print("read returns ", read(dp))        
        dp="Kellerschalter/V"
        print("read returns ", read(dp))
        dp="keller2/V"
        print("read returns ", read(dp))
        time.sleep(3)
        sys.exit()
        

    while 0:
        dp="wohnzimmer/XOR/11"
        print("read returns ", read(dp))
        print("write xor returns ", write(dp,1))
        time.sleep(3)
        print("write xor returns ", write(dp,1))
        
    while 0:
        dp="kellerschalter"
        write(dp, 0b10000000) 
        print(read(dp))
        time.sleep(3)
        
        write(dp, 0x00) #0100 0000
        print(read(dp))
        time.sleep(3)
        
        

    while 0:
        #dps=["kellerschalter/7", "kellerschalter/6", "kellerschalter"]

        #o = [read(dp) for dp in dps]
        
        #for dat in o:
        #    print (dat)
        #dp="Wohnzimmer/9"
        dp="Kueche/3"
            
        write(dp, True)
        time.sleep(1.1)
        print ("on kueche 3")

        write(dp, False)
        time.sleep(1.1)
        print ("off kueche 3")
        
    while 0:
        dp="Kueche"
            
        write(dp, [0x00, 0x04, 0x00])
        time.sleep(0.1)

        write(dp, [0x00, 0x00, 0x00])
        time.sleep(0.1)

        #s="x".join([str(p) for p in o])
    #print (s)
    #sys.exit()

    #o = [read_relais(devicename) for devicename in globals.config.DeviceSchalter]
    #    s=" ".join([" ".join([pp[0]+" is "+str(pp[1])+"; " for pp in p]) for p in o])
    #    print (str(datetime.datetime.now()),  " " , s)
        
    
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()

