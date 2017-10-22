#!/usr/bin/python3
import http.server
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

#die reader hier brauch ich fuer die listenerthreads
import readETH008 as ETH
import readPV as PV
import readHealth as HEALTH
import readtemp as TEMP
import readAlias as ALIAS
import readComp as COMP
import readDlms as DLMS
import readMOD as MOD
import readVar as VAR
import eventhandler

try:
    import readHM as HM
except:
    import readDummy as HM
    pass

import pvTimer
###import ETHserver

import psutil # needed for restart

    
PORT = 8000
ETHPORT = 17494

globals.shutdown = False
globals.restart = False
    
class readHandler(http.server.SimpleHTTPRequestHandler):
    
    @logged(logging.DEBUG)
    def readMulti(self, dps=""):
    
        return JSONHelper.encodeParm(driverCommon.readMulti(dps))


    
    def do_POST(self):
        #print(self.headers['content-length'])
        #print ('connect from %s;' % self.client_address[0])
        
        #if '/get' self.path
        #print (self.__dict__)
        length = int(self.headers['content-length'])
        data_string = self.rfile.read(length)
        try:
            result = readHandler.readMulti(self)
            #time.sleep(1)
        except socket.error as e:
            logging.exception("do_POST cannot read")        
            result = "error" + str(e)
        self.wfile.write(bytes(result, 'UTF-8'))

        
#---------------------------------------
#
#
    def sendMyHeader(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()

    @logged(logging.DEBUG)
    def do_GET(self):
        # syntax: http://kellerraspi:8000/read/bli/bla/?dp=pv/pv0bbb&ccc=ddd
        # http://kellerraspi.sigisoft.com:8000/read/bli/bla/?dp=[%22PV/PV0%22,%20%22PV/PV1%22,%20%22TEMP/00042b8679ff%22,%20%22TEMP/00042cb4d4ff%22,%20%22TEMP/00042d9aabff%22,%20%22ETH/kellerschalter/3%22,%20%22ETH/kellerschalter%22]        
                
        result = None        
        parsed=urllib.parse.urlparse(self.path)
        query = urllib.parse.unquote(parsed.query)
        
        query_components={'dp':""}

        try:
            query_list=query.split("&")
            query_components = dict(qc.split("=") for qc in query_list)
        except Exception as e: # no or not enough parameters:
            #logging.exception("server.do_GET no parameters found. need at least a dp")
            #getDatapointsArchive braucht keine parameters...
            #carry on with empty dp
            #print ("server: doGet Exception empty datapoint")
            pass

        timeout=10
        if "timeout" in query_components :
            timeout=JSONHelper.decodeParm(query_components["timeout"])
            
        n = -100 #for readArchive
        if "n" in query_components:
            n=JSONHelper.decodeParm(query_components["n"])
            
        operation = "" #for readArchive
        if "operation" in query_components:
            operation=JSONHelper.decodeParm(query_components["operation"])

        timeDelta = 0 #for readArchive
        if "timeDelta" in query_components:
            timeDelta=JSONHelper.decodeParm(query_components["timeDelta"])            
            if type(timeDelta) is str:
                if "none" == timeDelta:
                    timeDelta=None
                else:
                    try:
                        timeDelta = int(timeDelta)
                    except:
                        timeDelta=None
                    
            
        data = "" #for write
        if "data" in query_components:
            data=JSONHelper.decodeParm(query_components["data"])
            if data == '"false"' or data == 'false':
                data=False
                
            if data == '"true"' or data == 'true':
                data=True
                
            print("Server.py: got data ", data)

        pulse = None #for pulse write to eth boards.
        if "pulse" in query_components:
            pulse=JSONHelper.decodeParm(query_components["pulse"])
            print("Server.py: got pulse ", pulse)
            
        timeStampTo = None
        if "timeStampTo" in query_components:
            timeStampTo=JSONHelper.decodeParm(query_components["timeStampTo"])
            
        timeStamp = datetime.datetime.now().isoformat(" ")  #for readArchive
        if "timeStamp" in query_components:
            timeStamp=JSONHelper.decodeParm(query_components["timeStamp"])

        dp = ''
        if "dp" in query_components :
            dp = JSONHelper.decodeParm(query_components["dp"])
            print ("server.py: got dp ", dp)
            #if type(dp) is list:  # readmulti soll jsonified list erhalten
            #    dp=json.dumps(dp)

        print("1: dp is"  + str(dp))
        
        p=parsed.path.split("/")        
        if len(p)==0:
            p+=["", ""]
            
        #if p[1] != 'read':
        #    result = "<html><body><h1>NoNo</h1></html></body>"
            
        #print("result is %s" % str(result))
        
        if result is None:   # if there was an error, result is already filled.
            if p[1] == 'read':
                self.sendMyHeader()
                try:
                    dat = driverCommon.read(dp, timeout)
                    #print ("xxxserver.py: read returned %s" % str(dat))
                    result = JSONHelper.encodeParm(dat)
                    #print ("xxxserver.py: is result %s" % str(result))
                except Exception as e:
                    logging.exception("do_GET cannot read >>%s<<" % str(dp))        
                    result = "error " + str(e)            
                    
            elif p[1] == 'readMulti':
                self.sendMyHeader()
                try:
                    #print("server: readmulti dps %s" %dp)
                    dat = driverCommon.readMulti(dp, timeout)
                    #print ("xxxserver.py: read returned %s" % str(dat))
                    result = JSONHelper.encodeParm(dat)
                    #print ("xxxserver.py: is result %s" % str(result))
                except socket.error as e:
                    logging.exception("do_GET cannot multiRead >>%s<<" % str(dp))        
                    result = "error " + str(e)   

            elif p[1] == 'readMultiJ':
                self.sendMyHeader()
                try:
                    #print("server: readmultij dps %s" %dp)
                    dat = driverCommon.readMulti(dp, timeout)
                    #print ("xxxserver.py: read returned %s" % str(dat))
                    result = JSONHelper._encode(dat)
                    #print ("xxxserver.py: is result %s" % str(result))
                except socket.error as e:
                    logging.exception("do_GET cannot multiRead >>%s<<" % str(dp))        
                    result = "error " + str(e)   
                    
            elif p[1] == 'getInfoArchive':
                self.sendMyHeader()
                try:
                    dat = driverCommon.getInfoArchive(dp)
                    result = JSONHelper._encode(dat)
                    
                except socket.error as e:
                    logging.exception("do_GET cannot getInfoArchive >>%s<<" % str(dp))        
                    result = "error " + str(e)                        

            elif p[1] == 'getDatapointsArchive':
                self.sendMyHeader()
                try:
                    dat = driverCommon.getDatapointsArchive()
                    result = JSONHelper._encode(dat)
                    
                except socket.error as e:
                    logging.exception("do_GET cannot getDatapointsArchive.")        
                    result = "error " + str(e)                        
                    
            elif p[1] == 'readArchive':
                self.sendMyHeader()
                try:
                    #print("server: readArchiveJ - dps %s, %d, %s, %s" % (str(dp), n, str(timeDelta), timeStamp))
                    
                    dat = driverCommon.readArchive(dp, timeStamp, n, timeDelta, operation, timeStampTo)
                    result = JSONHelper.encodeParm(dat)
                    #print ("server:Readarchive returns ", result)
                    
                except socket.error as e:
                    logging.exception("do_GET cannot readArchive >>%s<<" % str(dp))        
                    result = "error " + str(e)                        

            elif p[1] == 'readArchiveJ':
                self.sendMyHeader()
                try:
                    #print("server: readArchiveJ - dps %s, %d, %s, %s" % (str(dp), n, str(timeDelta), timeStamp))
                    # timeStampTo auf Verdacht; wird aber derzeit nicht uebergeben.
                    dat = driverCommon.readArchive(dp, timeStamp, n, timeDelta, operation, timeStampTo)
                    result = JSONHelper._encode(dat)
                    
                    #print ("server:ReadarchiveJ returns ", result)
                    
                except socket.error as e:
                    logging.exception("do_GET cannot readArchive >>%s<<" % str(dp))        
                    result = "error " + str(e)                        

            elif p[1] == 'readArchiveMultiJ':
                self.sendMyHeader()
                try:
                    print("server: readArchiveMultiJ - dps %s, %d, %s, %s" % (str(dp), n, str(timeDelta), timeStamp))
                    dat = driverCommon.readArchiveMulti(dp, timeStamp, n, timeDelta, operation, timeStampTo)
                    result = JSONHelper._encode(dat)
                    
                    #print ("server:ReadarchiveJ returns ", result)
                    
                except socket.error as e:
                    logging.exception("do_GET cannot readArchive >>%s<<" % str(dp))        
                    result = "error " + str(e)                        
                    
            elif p[1] == 'write':
                self.sendMyHeader()
                try:
                
                    print("server.py: write dps %s, %s" % (dp, str(data)))                    
                    dat = driverCommon.write(dp, data, pulse)
                    result = JSONHelper._encode(dat)
                except socket.error as e:
                    logging.exception("do_GET cannot write >>%s<<" % str(dp))        
                    result = "error " + str(e)   
            else:
                #propagate:
                return super().do_GET()
        else:
            return super().do_GET()
            
        self.wfile.write(bytes(result, 'UTF-8'))
            

#-----------------------------------------------

def start_server(port):
    try:
        Handler = readHandler
        globals.httpd = socketserver.TCPServer(("", port), Handler)
        print("serving at port", port)
        #while not globals.shutdown:
        globals.httpd.serve_forever()
            
    except socket.error as e:
        logging.exception("unable to serve port %d; error %s" % (port, e))
        print ("unable to serve port %d; error %s" % (port, e))
        globals.shutdown = True
        globals.restart = True
        
    logging.error("finishing serverthread")
    print ("finishing serverthread")


#------------------------------------------------------------
#
# from http://stackoverflow.com/questions/11329917/restart-python-script-from-within-itself
#
#
def restart_program():
    """Restarts the current program, with file objects and descriptors
       cleanup
    """

    try:
        p = psutil.Process(os.getpid())
        for handler in p.get_open_files() + p.connections():
            os.close(handler.fd)
    except Exception as e:
        logging.exception("restart_program")

    python = sys.executable
    os.execl(python, python, *sys.argv)

#----------------------------------------------------------------------------------------------------
# tryToStart:
#   versucht den listener von mymodul zu starten (wenn es den gibt)

@logged(logging.DEBUG)
def tryToStart(myListener, threadArgs, myName):
    rv = None
    try: # versuche alle listener aller Module zu starten
        rv = threading.Thread(target=myListener, args = threadArgs, name=myName)
        rv.daemon = True
        rv.start()    
    except:
        pass
        
    return rv
    
    
if __name__ == "__main__":
    with config.configClass() as configuration:
        globals.gConfig= configuration  #brauch ichs noch???
        globals.config= configuration   
        print ("metadata: start - with - debug")
        #logging.getLogger().setLevel(logging.DEBUG)
        
        config.createPID("/run/PVserver.pid")
        try:
            runningThreads = []

            t = threading.Thread(target=start_server, args = (PORT, ), name="PVServer")
            t.daemon = True
            t.start()
            runningThreads.append(t)
            
            t2 = threading.Thread(target=pvTimer.pvTimerSetUp, args = (0, ), name="pvTimer")
            t2.daemon = True
            t2.start()
            runningThreads.append(t2)

            #t3 = threading.Thread(target=ETHserver.start_ETHserver, args = (ETHPORT, ), name="ETHServer")
            #t3.daemon = True
            #t3.start()
            #runningThreads.append(t3)
            
            for modul in [ETH, PV, HEALTH, TEMP, ALIAS, COMP, DLMS, MOD, VAR, HM, eventhandler]:
                try:
                    thread=tryToStart(modul.worker, (0, ), modul.__name__)
                    if thread is not None:
                        runningThreads.append(thread)
                        print ("starting %s" % thread.name)
                except:
                    pass # die function hats nicht gegeben. macht nix.
                    
                
            
            while (not globals.shutdown):
                time.sleep(10)
                #check ob noch alle listenerthreads laufen, sonst shutdown!
                for t in runningThreads:
                    if not t.is_alive():
                        logging.error("thread %s stopped" % t.name)                        
                        print ("server: thread %s stopped - stopping myself" % t.name)                        
                        globals.shutdown = True
                        
            for t in runningThreads: # 10 sec warten bis alle tot sind
                t.join(10.0)
            
            try:
                globals.httpd.shutdown()
                globals.httpd.server_close()
            except:  # is ma wuascht, wenn httpd nicht hochgekommen ist.
                pass
                
            print ("2- shutdown issued")
            logging.error("shutdown issued...")
                
        finally:
            os.unlink("/run/PVserver.pid")

        #nicht neu starten, da mich der watchdog sowieso killt
        # sonst wird der usbstick korrpumpiert...
        #if  globals.restart:
            #restart_program()
            # klappt irgendwie nicht, watchdog toetet die maschine (wg. pidfile?)
            # port 8000 ist auch besetzt...
            # prozess wird aber neu gestartet
            

