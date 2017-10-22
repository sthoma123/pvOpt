#!/usr/bin/python3
#
# this is the small commanline tool for minimal modbus: 
# all parms can be given in the commandline, if not the user is prompted.
#
#
import os, glob, time, sys, datetime
import http, http.client
import json
import config
import globals
from funcLog import logged
import logging
import minimalmodbus
import sys

def get1Parm(p, id, prompt, default):
    # check if id present
    rv = ""
    
    if id in p:
        rv = p[id]
    else:
        # otherwise ask user given default
        rv = input("%10s-%s [%s]: " % (id,  prompt, default)) 
        if rv == "":
            rv = default
            
    return rv
    
def parseParm(args):
    print (args)
    rv = dict()
    for a in args:
        id  = ""
        val = ""
        tu  = a.split("=")
        if len(tu) == 1:
            val=tu[0]
            
        if len(tu) > 1:
            id=tu[0]
            val=tu[1]
            
        rv[id]=val    
    return rv

#---------------------------------------------------------------------
def myToInt(v):
    rv = 0
    try:
        rv=int(v)
    except:
        print ("Unable to convert %s to integer" % (str(v)))
        
    return rv

    #---------------------------------------------------------------------
def myToFloat(v):
    rv = 0
    try:
        rv=float(v)
    except:
        print ("Unable to convert %s to float" % (str(v)))
        
    return rv

def main():
    rv = 0
    
    p = parseParm(sys.argv[1:])    
    baudrate = get1Parm(p, "baudrate", "Baudrate", "9600")
    bits = get1Parm(p, "bits", "Bits", "8")    
    parity = get1Parm(p, "parity", "Parity", "N")    
    stop = get1Parm(p, "stop", "Stopbits", "1")    
    timeout = get1Parm(p, "timeout", "Timeout in seconds", "1.0")
    dev = get1Parm(p, "device", "serial device", "ttyUSB0")
    slaveid = get1Parm(p, "slaveid", "Slave- (Modbus-) ID", "1")
    function=get1Parm(p, "function", "Modbus function (2 - read discrete, 1 - read coils, 4 - read input register, 3 read holding register, 5 write single coil, 6 - write single register, 16 - write multiple registers 15 write multiple coils, ", "4")
    datatype = get1Parm(p, "datatype", "Datatype (f-float, i-int, b-byte, s-string, l-long, bit, register, registers)", "f")
    
    numberOfRegisters = 32
    if datatype == "registers" or datatype == "s":
        numberOfRegisters = myToInt(get1Parm(p, "numberOfRegisters", "Numer of registers", "32"))

    function = myToInt(function)
    slaveid = myToInt(slaveid)
    
    if function == 2 or function == 1 or function == 4 or function == 3:
        readwrite = "r"
    else:
        readwrite = "w"
        
    if readwrite == "w":
        value=get1Parm(p, "value", "Value", "")
        
    if readwrite == "w" and datatype == "f":
        numberOfRegisters = myToInt(get1Parm(p, "numberOfRegisters", "Numer of registers", "2"))
        
    address = get1Parm(p, "address", "Register Address", "1")
    address = myToInt(address)
    
    #readwrite = get1Parm(p, "readwrite", "read(r) or write (w)", "r")
    
    instrument = 0

    try:
        #instrument = minimalmodbus.Instrument('/dev/ttyUSB0', slaveid) # port name, slave address (in decimal, 0==broadcast)
        instrument = minimalmodbus.Instrument('/dev/' + dev, slaveid) # port name, slave address (in decimal, 0==broadcast)

        #print (dir(instrument))
        
        instrument.serial.parity = parity
        instrument.serial.stopbits= myToInt(stop)
        instrument.serial.bytesize= myToInt(bits)
        instrument.serial.timeout = myToFloat(timeout)
        instrument.serial.baudrate = myToInt(baudrate)
        
        instrument.debug = True
        # doc see: https://minimalmodbus.readthedocs.org
        
        if readwrite == "r":
            if datatype == "bit":
                rv = instrument.read_bit(address, function)
            elif datatype == "f":
                rv = instrument.read_float(address, function, 2)
            elif datatype == "l": #32 bit registeraddress, functioncode=3 or 4, signed=False)
                rv = instrument.read_long(address, function, True)
            elif datatype == "ul": #32 bit registeraddress, functioncode=3 or 4, signed=False)
                rv = instrument.read_long(address, function, False)
            elif datatype == "register": #16 bit registeraddress, numberOfDecimals=0, functioncode=3, signed=False)
                rv = instrument.read_register(address, 0, function, True) 
            elif datatype == "uregister": #16bit registeraddress, numberOfDecimals=0, functioncode=3, signed=False)
                rv = instrument.read_register(address, 0, function, False) 
            elif datatype == "registers": # registeraddress, numberOfRegisters, functioncode=3
                rv = instrument.read_registers(address, numberOfRegisters, function) 
            elif datatype == "s": #registeraddress, numberOfRegisters=16, functioncode=3)
                rv = instrument.read_string(address, numberOfRegisters, function) 
        else:
            rv = ""
            if datatype == "bit":  #registeraddress, value, functioncode=5)
                instrument.write_bit (address, myToInt(value), function)
            elif datatype == "f": # registeraddress, value, numberOfRegisters=2)
                instrument.write_float (address, myToFloat(value), numberOfRegisters)
            elif datatype == "l": # vregisteraddress, value, signed=False)[
                instrument.write_long (address, myToInt(value), True)
            elif datatype == "ul": # vregisteraddress, value, signed=False)[
                instrument.write_long (address, myToInt(value), False)
            elif datatype == "register": #(registeraddress, value, numberOfDecimals=0, functioncode=16, signed=False)
                instrument.write_register (address, myToInt(value), 0, function, True) 
            elif datatype == "register": #(registeraddress, value, numberOfDecimals=0, functioncode=16, signed=False)
                instrument.write_register (address, myToInt(value), 0, function, False) 
            elif datatype == "registers": #(registeraddress, values)
                instrument.write_registers (address, [myToInt(x) for x in values.split(",")] )
            elif datatype == "s": #registeraddress, textstring, numberOfRegisters=16)
                instrument.write_string (address, value, numberOfRegisters)
                
        if rv != "":
            print ("Modbus %d:%d returned: %s " % (slaveid, address,rv))
        
        #print (slaveid)
        #print (instrument.read_register(0, 4)) 
        #for i in range (0,126):            
        #    print (2*i, instrument.read_float(2*i, 4, 2)) 
#        print (instrument.read_float(2, 4, 2)) 
#        print (instrument.read_float(4, 4, 2)) 
        
    except IOError as e:
        print ("IOError")
        pass


    return rv
    
    #instrument.debug = True
    #print (instrument)


    #print ("Address, value")
    #for addr in range(0,255):
    #    try:
    #        by = instrument.read_register(addr, 0)
    #        print ("%7d, %4x" % (addr, by))
    #    except IOError as e:
    #        pass
            
#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
#    gConfig=configuration
    globals.config= configuration
    # print list of available parameters.
    
    main()
    

    
    
