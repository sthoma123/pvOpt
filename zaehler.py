
from __future__ import print_function 
import serial
import time
import os, sys, datetime

#See here python code that reads the meter data about every 5 seconds and writes a line to file is the meter data has changed. It uses py-serial.

def send(port, msg, tr):
  """ sends an command to serial and reads and checks the echo
      port  - the open serial port
      msg - the string to be send
      tr    - the responce time
  """
  print("start send %s" % msg)   
  port.write(bytes(msg, 'UTF-8'))
  print("send.written 1")  
  time.sleep(tr)
  print("send.written 2")  
  #echo = port.read(len(msg))
  #print("send.written 3")  
  #if (echo != msg):
  #  print("just sent %s of %s msg" % (str(echo), str(msg)))
    
    
  print("end send %s msg" % str(msg))

def read_datablock():
  ACK = '\x06'
  STX = '\x02'
  ETX = '\x03'
  tr = 0.2
  """ does all that's needed to get meter data from the meter device """ 
  try:
    serPort=serial.Serial(port='/dev/ttyUSB0', baudrate=300, bytesize=7, parity='E', stopbits=1, timeout=1.5); # open port at specified speed
    print ("1")
    # 1 ->
    time.sleep(tr)
    print ("2")
    Request_message='/?!\r\n' # IEC 62056-21:2002(E) 6.3.1
    send(serPort, Request_message, tr)
    print ("3")
    # 2 <-
    time.sleep(tr)
    Identification_message=serPort.readline() # IEC 62056-21:2002(E) 6.3.2
    print ("got ", Identification_message)
    if (Identification_message[0] != '/'):
      print("no Identification message")
      serPort.close()
      return ""
    if (len(Identification_message) < 7):
      print("Identification message to short")
      serPort.close()
      return ""
    if (Identification_message[4].islower()):
      tr = 0.02
    manufacturers_ID = Identification_message[1:4]
    if (Identification_message[5] == '\\'):
      identification = Identification_message[7:-2]
    else:
      identification = Identification_message[5:-2]
    speed = Identification_message[4]
    #print("speed = ", speed)
    if (speed == "1"): new_baud_rate = 600
    elif (speed == "2"): new_baud_rate = 1200
    elif (speed == "3"): new_baud_rate = 2400
    elif (speed == "4"): new_baud_rate = 4800
    elif (speed == "5"): new_baud_rate = 9600
    elif (speed == "6"): new_baud_rate = 19200
    else:
      new_baud_rate = 300
      speed = "0"
    print(manufacturers_ID, " ", identification, " speed=", speed)
    # 3 ->
    Acknowledgement_message=ACK + '0' + speed + '0\r\n' # IEC 62056-21:2002(E) 6.3.3
    send(serPort, Acknowledgement_message, tr)
    print ("4")
    serPort.baudrate=new_baud_rate
    time.sleep(tr)
    # 4 <-
    datablock = ""
    print ("5")
    if (serPort.read() == STX):
      x = serPort.read()
      BCC = 0
      while (x  != '!'):
        BCC = BCC ^ ord(x)
        datablock = datablock + x
        x = serPort.read()
      while (x  != ETX):
        BCC = BCC ^ ord(x) # ETX itself is part of block check
        x = serPort.read()
      BCC = BCC ^ ord(x)
      x = serPort.read() # x is now the Block Check Character
      # last character is read, could close connection here
      if (BCC != ord(x)): # received correctly?
        datablock = ""
        print("Result not OK, try again")
    else:
      print("No STX found, not handled.")
    serPort.close()
    return datablock
  except Exception as e:
    print("Error reading serial data <<%s>>" % str(e))
    if (serPort.isOpen()):
      serPort.close()      
    return ""

def meter_data(datablock, map, header):
  """ takes a datablock as received from the meter and returns a list with requested meter data as set in map
      if header != 0 a list with data type and units is returned """
  line = []
  ## initialise line
  for l in range(len(map)):
    if (header == 1):
      line.append(map[l][1])
    elif (map[l][0] == "time"):
      line.append(time.strftime("%Y-%m-%d %H:%M:%S"))
    else:
      line.append("")
  datasets = datablock.split('\n')
  for dataset in datasets:
    if (dataset != ""):
      x = dataset.split('(')
      address = x[0]
      x = x[1][:-2].split(' ') # the standard seems to have a '*' instead of ' ' here
      value = x[0]
      try:
        unit = '['+x[1]+']'
      except:
        unit = ""
      for l in range(len(map)):
        if (map[l][0] == address):
          if (header == 0):
            line[l] = value
          else:
            line[l] = map[l][1] + unit
          break;
  return line

def output(filename, line):
  f = open(filename, "a")
  print(line, file=f)
  f.close()

map = [
  # The structure of the meter_data() output can be set with this variable 
  # first string on each line is the cosim adress of the data you want to safe or "time" to insert the time
  # the second string on each line is a description of the type of data belonging to the cosim address
  # the order of the lines sets the order of the meter_data() output
  # example
  # header: ['meter ID', 'datum & tijd', 'verbruik totaal[kWh]', 'verbruik tarief1[kWh]', 'verbruik tarief2[kWh]', 'terug totaal[kWh]', 'terug tarief1[kWh]', 'terug tarief2[kWh]']
  # data: ['12345678', '2013-02-08 10:08:41', '0054321', '0000000', '0054321', '0000000', '0000000', '0000000']
  ["1-0:0.0.0*255", "meter ID"],
  ["time", "datum & tijd"],
  ["1-0:1.8.0*255", "verbruik totaal"],
  ["1-0:1.8.1*255", "verbruik tarief1"],
  ["1-0:1.8.2*255", "verbruik tarief2"],
  ["1-0:2.8.0*255", "terug totaal"],
  ["1-0:2.8.1*255", "terug tarief1"],
  ["1-0:2.8.2*255", "terug tarief2"]
]
