#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß

print ("imported " + __name__)

import minimalmodbus

instrument=0
validDevice=[""]

bereich = list()
#bereich += list(range(1,20))
bereich += list(range(100,120))
for id in bereich :
	try:

		#instrument = minimalmodbus.Instrument('/dev/ttyUSB0', slaveid) # port name, slave address (in decimal, 0==broadcast)
		instrument = minimalmodbus.Instrument('/dev/ttyUSB0',id ) # port name, slave address (in decimal, 0==broadcast)

		#print (dir(instrument))

		instrument.serial.parity = "N"
		instrument.serial.stopbits= 1
		instrument.serial.bytesize= 8
		instrument.serial.timeout = 1.0
		instrument.serial.baudrate = 9600

		instrument.debug = False
		#print (id)
		#print (instrument.read_register(0, 4))
		#print (id)
		for i in range (0,4, 1):
            # read_float(registeraddress, functioncode=3, numberOfRegisters=2)
			# print (id,   i, "Ok", instrument.read_float(i,3, 4))
            
            # read_register(registeraddress, numberOfDecimals=0, functioncode=3, signed=False)[source]
			print (id,   i, "Ok", instrument.read_register(i, 0, 3))
            
	#        print (instrument.read_float(2, 4, 2))
	#        print (instrument.read_float(4, 4, 2))
		validDevice = validDevice + [id]

	except IOError as e:
		#print ("IOError", str(e))
		print (id, "NOT Ok")
		pass

print ("valid are ", validDevice)
