#!/usr/bin/python3

import minimalmodbus

instrument=0

for id in range(247) :
	try:

		#instrument = minimalmodbus.Instrument('/dev/ttyUSB0', slaveid) # port name, slave address (in decimal, 0==broadcast)
		instrument = minimalmodbus.Instrument('/dev/ttyUSB0', id) # port name, slave address (in decimal, 0==broadcast)

		#print (dir(instrument))

		instrument.serial.parity = "N"
		instrument.serial.stopbits= 1
		instrument.serial.bytesize= 8
		instrument.serial.timeout = 1.0
		instrument.serial.baudrate = 19200

		instrument.debug = True
		#print (slaveid)
		#print (instrument.read_register(0, 4))

		for i in range (6,7):
			print (id, 2*i, instrument.read_float(2*i, 3, 2))
	#        print (instrument.read_float(2, 4, 2))
	#        print (instrument.read_float(4, 4, 2))
		print ("id %d OK" % (id))
		break
	except IOError as e:
		print ("id %d IOError" % (id), str(e))
		pass

