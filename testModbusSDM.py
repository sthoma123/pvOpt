#!/usr/bin/python3
import minimalmodbus, sys, time

instrument=0
# 8E1 2400 ist default fuer sdm120

bauds = (2400, )
parities=("N", )
#registers=(0,6,12,18,30,70,72,74,76,78,80,82,84,86,88,90,92,94,258,264,342,344)
registers=range(0, 1)
#, 0xe1, 0x46, 0x48, 0x4a, 0x0156)


for slaveid in range (10,20):
    try:
        # port name, slave address (in decimal, 0==broadcast)
        instrument = minimalmodbus.Instrument('/dev/ttyUSB.modbus', slaveid) 
        #instrument = minimalmodbus.Instrument('/dev/ttyUSB.modbus', 1) # port name, slave address (in decimal, 0==broadcast)
        
        instrument.serial.stopbits= 1
        instrument.serial.bytesize= 8
        instrument.serial.timeout = 1.0

        #print (dir(instrument))
        for par in parities:
            instrument.serial.parity = par
            for baud in bauds:
                instrument.serial.baudrate = baud
        
                instrument.debug = True
                print (slaveid)
                #print (instrument.read_register(0, 4)) 
                for i in registers:
                    try:
                        s= "(%d%s%d  %d: %d, %d)  "%(instrument.serial.bytesize, instrument.serial.parity, 
                                instrument.serial.stopbits, instrument.serial.baudrate, slaveid, i)
                        sys.stdout.write(s)
                        print (i, instrument.read_float(i, 4, 2)) 
                        time.sleep(0.2)
                        
                    except ValueError as e:
                        print ("inner ValueError: ", e)
                    
                    except IOError as e:
                        print ("inner IOError")

#        print (instrument.read_float(2, 4, 2)) 
#        print (instrument.read_float(4, 4, 2)) 
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
        
