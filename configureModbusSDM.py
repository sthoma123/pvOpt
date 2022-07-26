#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#
# konfiguriert Slave-ID eines SDM120. 
#
# ACHTUNG: Set button on device mindestens 5 sek druecken bis -set- im display steht!!!
#
#
#
print ("imported " + __name__)
import minimalmodbus, sys

serialdevs=('/dev/ttyUSB.modbus',)
bauds=(2400,  )
registers=(0x014,  )
parities=("N", )
stopbits=1
bytesize=8
timeout=1.0


def writeToTarget(targetdev, serialdev, sourceid, baud, parity):

    # port name, slave address (in decimal, 0==broadcast)
    instrument = minimalmodbus.Instrument(serialdev, sourceid) 
    
    instrument.serial.stopbits= 1
    instrument.serial.bytesize= 8
    instrument.serial.timeout = 1.0
    instrument.serial.parity = parity
    instrument.serial.baudrate = baud
    
    instrument.debug = False

    if True:
        f=float(targetdev)
        print ("write id as float: ", f)
        instrument.write_float(0x0014, f) #use modbus code 16
    
    found = probeSourcedev(targetdev)

    if False:
        addrs = (0x0014, )
        for addr in addrs:
            print ("read %d:" % addr)
            try:
                response = instrument.read_float(addr, functioncode=3, numberOfRegisters=2)
                print ("read ok, returned ", response)
            except IOError as e:
                print ("inner IOError")
                pass
    

#------------------------------------------------------------------------
# retourniert gueltige config
#
def probeSourcedev(slaveid):
# lese spannung (register 0 in allen  kombinationen)
    baud = bauds[0]
    parity = parities[0]
    register = registers[0]
    found = False
    serialdev = serialdevs[0]
    if False:
        #nimm das erste blind...
        found = True
    else:
        for serialdev in serialdevs:
            for baud in bauds:
                for paritiy in parities:
                    for register in registers:
                        # port name, slave address (in decimal, 0==broadcast)
                        instrument = minimalmodbus.Instrument(serialdev, slaveid) 
                        
                        instrument.serial.stopbits= 1
                        instrument.serial.bytesize= 8
                        instrument.serial.timeout = 1.0
                        instrument.serial.parity = parity
                        instrument.serial.baudrate = baud
                        instrument.debug = False
                        try:
                            if found:
                                break
                            s= "probe (%d%s%d  %d: slaveID:%d, register:%d)  "%(instrument.serial.bytesize, instrument.serial.parity, 
                                    instrument.serial.stopbits, instrument.serial.baudrate, slaveid, register)
                            sys.stdout.write(s)
                            response=instrument.read_float(register, functioncode=3, numberOfRegisters=2)
                            print (register, response) 
                            found = True
                        except ValueError as e:
                            #print ("inner ValueError: ", e)
                            pass
                        
                        except IOError as e:
                            #print ("inner IOError")
                            pass
                        if found:
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break

            
    return found, serialdev, slaveid, baud, parity, register
            
#------------------------------------------------------------------------
#
def usage():
    print ("Usage:")
    print ("   configureModbusSDM.py  [oldDeviceID=1], <newDeviceID>")

#------------------------------------------------------------------------

#main:

#print ('Number of arguments:', len(sys.argv), 'arguments.')
if len(sys.argv) < 1:
    usage()
else:
    #print ('Argument List:', str(sys.argv))
    sourcedev = 1
    targetdev = 1
    if len (sys.argv) > 2: #source and target supplied
        sourcedev = int(sys.argv[1])
        targetdev = int(sys.argv[2])
    elif len(sys.argv) > 1:
        targetdev = int(sys.argv[1])
        
    if sourcedev == targetdev:
        usage()
    else:
        found, serialdev, slaveid, baud, parity, register = probeSourcedev(sourcedev)
        if not found:
            print ("Unable to probe device %d - no answer from this device" % (sourcedev))
        else:
            print ("Ok to program device %d -> %d on %s" % (slaveid, targetdev, serialdev))
            try:
                input("Press enter to continue")
            except SyntaxError:
                pass
                
            writeToTarget(targetdev, serialdev, slaveid, baud, parity)
    
    