#!/usr/bin/python3

import minimalmodbus

instrument=0

for id in range(1,16):
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
		
		#print (slaveid)
		#print (instrument.read_register(0, 4))
		#for i in range (100,110):
		for i in range (0,50):
			print (id,i, instrument.read_float(2*i,4,2))
	#        print (instrument.read_float(2, 4, 2))
	#        print (instrument.read_float(4, 4, 2))

	except IOError as e:
		print ("IOError", str(e))
		pass

