#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß

#
# server for ETH8020 and similar on port 17494
# uses a binary protocol
#
# OBSOLETE: now contained in readETH with the listener-Thread
#
#    
#Following customer requests for obtaining input states without the need for polling the ETH8020, this can be achieved with the existing input mapping function.
#If you would like the inputs to be mapped to a custom device then we have a simple command structure to achieve this, the ETH8020 will send the commands in blue, your device will
#respond with commands in yellow.
#A TCP packet with 0x79 (password entry) in the first byte, then the following bytes will be the password supplied above
#To acknowledge a password match, respond with 1, else send 2
#Digital active (0x20) or Digital inactive (0x21) followed by the output number
#Reply with a 0 for success, else send 1
#Note that the complete sequence must be followed, even if the password fails.
#
#
#

print ("imported " + __name__)

import socketserver
import socket

import os, time, sys, datetime
import config
import logging
import globals
import driverCommon
import json

import queue
import threading
import urllib.parse
from funcLog import logged
import JSONHelper
import pvTimer

import psutil # needed for restart

    
PORT = 17494
    
import socketserver

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
        
        if state and (switch == 4): #wohnzimmer unten
            schalteLeinwand();
        
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
            
    
#-----------------------------------------------

def start_ETHserver(port):
    try:
        # Create the server, binding to localhost on port x
        globals.ETHserver = socketserver.TCPServer(("", port), ETHHandler)
        print ("starting server at port  %d" % (port))

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

    
    
if __name__ == "__main__":
    with config.configClass() as configuration:
        globals.config= configuration   
        
        
        #print ("metadata: start - with - debug")
        #logging.getLogger().setLevel(logging.DEBUG)
        
        config.createPID("/run/PVETHserver.pid")
        try:
            t = threading.Thread(target=start_ETHserver, args = (PORT, ))
            t.daemon = True
            t.start()
            
            while (not globals.shutdown):
                time.sleep(10)
                
            print ("1- shutdown issued; shutdown ETHServer")
            
            try:
                globals.ETHserver.shutdown()
            except:  # is ma wuascht, wenn httpd nicht hochgekommen ist.
                pass
                
            print ("2- shutdown issued; shutdown httpd")
            logging.error("shutdown issued...")
                
        finally:
            os.unlink("/run/PVETHserver.pid")

