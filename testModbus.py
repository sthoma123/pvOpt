#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß

print ("imported " + __name__)
import minimalmodbus
import time

instrument=0

for slaveid in range (0,247):
    try:
        #instrument = minimalmodbus.Instrument('/dev/ttyUSB0', slaveid) # port name, slave address (in decimal, 0==broadcast)
        #instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1) # port name, slave address (in decimal, 0==broadcast)
        instrument = minimalmodbus.Instrument('/dev/ttyUSB.modbus', 1) # port name, slave address (in decimal, 0==broadcast)

        print (dir(instrument))
        
        instrument.serial.parity = "N"
        instrument.serial.stopbits= 1
        instrument.serial.bytesize= 8
        instrument.serial.timeout = 1.0
        instrument.serial.baudrate = 9600
        
        instrument.debug = True
        #print (slaveid)
        #print (instrument.read_register(0, 4)) 
        for i in range (0,126):            
            time.sleep(2)
            print (2*i, instrument.read_float(2*i, 4, 2)) 
#        print (instrument.read_float(2, 4, 2)) 
#        print (instrument.read_float(4, 4, 2)) 
        break
    except IOError as e:
        print ("IOError")
        pass


#instrument.debug = True
#print (instrument)


#print ("Address, value")
#for addr in range(0,255):
#    try:
#        by = instrument.read_register(addr, 0)
#        print ("%7d, %4x" % (addr, by))
#    except IOError as e:
#        pass
        
