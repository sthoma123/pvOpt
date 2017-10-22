
#!/usr/bin/python3
#28-00042b8679ff  28-00042b868bff  28-00042d9aabff  28-00042d9bdaff  28-00042d9cc1ff 

import os, glob, time,  sys, datetime
import socket    # used for TCP/IP communication

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
#3A     ASCII text commands (V4+) - allows a text string to switch outputs, see section below
#77     Get serial number - Returns the unique 6 byte MAC address of the module.
#78     Get Volts - returns relay supply voltage as byte, 125 being 12.5V DC
#79     Password entry - see TCP/IP password
#7A     Get unlock time - see section below 
#7B     Log out - immediately re-enables TCP/IP password protection


 
# Prepare 3-byte control message for transmission
 



#----------------------------------------------------------------------------------------------------
def io_relais_raw(box, message): #network name of device
    TCP_PORT = 17494
    BUFFER_SIZE = 80
    try:
        # Open socket, send message, close socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((box, TCP_PORT))
        s.send(bytes(message,"UTF8"))
        cont = s.recv(BUFFER_SIZE)
        s.close()
    except:
        print ('unable to retrieve data from ' + box)
        print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
        return None
    return cont

#----------------------------------------------------------------------------------------------------
def read_relais_raw(box): #network name of device
    message = '\x24\x00\x00' # read Relays 
    return ord(io_relais_raw(box, message))

#----------------------------------------------------------------------------------------------------
def read_relais(box):
    r=read_relais_raw(box)
    rv = box+"."+str(i), temp, "deg", datetime.datetime.now()     
    return rv

#----------------------------------------------------------------------------------------------------
def set_relais (box, switch, state):
    if state:
      message = '\x20'
    else:
      message = '\x21'
    message += str(chr(switch)) + "\x00"
    return io_relais_raw(box, message)
    

#----------------------------------------------------------------------------------------------------
# MAIN:
#
devicenames = ["kellerschalter"]


while 1:
    p= [read_relais(devicename) for devicename in devicenames]
    print (str(datetime.datetime.now()),  " ".join([pp[0] + " " + str(pp[1]) for pp in p]))
    time.sleep(10)

