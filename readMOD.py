#!/usr/bin/python3
#---------------------------------------------------------------------------# 
# import the various modbus client implementations
#---------------------------------------------------------------------------# 

import os, glob, time,  sys, datetime
import threading
import config
import globals
from funcLog import logged
import logging
#from pymodbus.client.sync import ModbusTcpClient as ModbusClient
#from pymodbus.client.sync import ModbusUdpClient as ModbusClient
#from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import minimalmodbus as mmRtu
import metadata



#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def _read_mod_raw(device, register): #network name of device
    try:
        rq = client.write_registers(1, [10]*8)
        rr = client.read_input_registers(1,8)
        assert(rq.function_code < 0x80)     # test that we are not an error
        assert(rr.registers == [10]*8)      # test the expected value

        rq = client.readwrite_registers(1, [20]*8)
        rr = client.read_input_registers(1,8)
        assert(rq.function_code < 0x80)     # test that we are not an error
        assert(rr.registers == [20]*8)      # test the expected value
    except:
        #print ('unable to retrieve data from ' + wechselrichter)
        #print ("ErrorNumber: " + ErrorNumber + " " + ErrorMessage)
        return None
    return cont

#----------------------------------------------------------------------------------------------------
# opens modbus port
#
def openModPort(port):
# modbus port is e.g. [MOD/TTYUSB0]
# needs timeout and baudrate

    rv = None

    co=globals.gConfig.__dict__
    timeout = 0.2
    baudrate=19200
    coKey="MOD/%s" % (port)
    
    if coKey in co:
        if "timeout" in co[coKey]:
            timeout=float(co[coKey]["timeout"])
        if "baudrate" in co[coKey]:
            baudrate=int(co[coKey]["baudrate"])
        

    try:
        mmc=mmRtu.Instrument("/dev/" + port, 234)  # port name, slave address
        if  mmc is None:        
            logging.error ("readMOD.py: openPort; does not return a valid mmc object for %s " %(port))
            raise IOError ("openModPort: mmc is None")
        else:
            mmc.serial.close()  # sonst erfangt er sich nicht von einem IOError... (Close checkt ob er open ist)
            mmc.serial.open()
            
            mmc.serial.baudrate=baudrate
            mmc.serial.timeout=timeout
            mmc.debug = False
            #mmc.debug = True
            #mmc.close_port_after_each_call = True
        
            #globals.MODport[port] = mmc
        rv = mmc
        
    except IOError as e:
        logging.exception ("readMOD.py: Unable to open port %s (%s)" %(port, str(baudrate)))
        rv = None
    except OSError as e:  #OSError: [Errno 24] Too many open files: 
        logging.exception ("readMOD.py: OSError exception for port %s (%s)" %(port, str(baudrate)))
        # force myself to restart process
        rv = None        
        if e.errno == 24:
            globals.restart=True
            globals.shutdown=True
        

        
    return rv

#----------------------------------------------------------------------------------------------------
# reads modbus port
# takes list or string: /port/modbusID/boxtype/parmname/
# port, id und 
@logged(logging.DEBUG)
def read_mod_raw(port, modbusID, boxtype, parmname, default): 
    rv= None
    retry = 3
        
    co=globals.gConfig.__dict__
    slaveID = int(modbusID)
    register = parmname
    datalen = 2
    dataType = "INT"
    modbusCommand= 3

    dp = "MOD/%s/%s/%s/%s" %(port, modbusID, boxtype, parmname)
    unit = default[2]
    desc = default[0]
    if len(desc) == 0:  #eventuell gibts die metadaten vom uebersetzten datenpunkt
        default = metadata.read(dp, dp)
        unit = default[2]
        desc = default[0]
    


    keyBoxtype="MOD/%s" % (boxtype)
    if keyBoxtype in co: #use config from .ini file (otherwise assume it's just a modbus address)
        #parmdefinition is:
        #P1Volt=4,0,2,FLOAT,V
        parmDefinition=""
        
        if parmname in co[keyBoxtype]:
            parmDefinition=co[keyBoxtype][parmname].split(",")
        else:
            logging.error("did not find %s in definitions of %s" %(parmname, keyBoxtype))
            logging.error(str(co))
            
        if len(parmDefinition) > 0:
            modbusCommand = int(parmDefinition[0])
        if len(parmDefinition) > 1:
            register = int(parmDefinition[1])
        if len(parmDefinition) > 2:
            datalen = int(parmDefinition[2])
        if len(parmDefinition) > 3:
            dataType  = parmDefinition[3]
        if len(parmDefinition) > 4:
            unit = parmDefinition[4]
            
        if len(desc) == 0:
            desc = "%s of %s %s" %(parmname, boxtype, modbusID)
      
        #print ("modbuscommand = %d, register=%d, datalen=%d, datatType=%s, unit=%s" % (modbusCommand, register, 
        #        datalen, dataType, unit))

    #if port not in globals.MODport:    
    #    openModPort(port)

    try:
        mmc = openModPort(port)
        if mmc is None:
            globals.modbusQuality = globals.modbusQuality - 10        
            desc = "mmc=None for %s" % port
            rv= desc, 0, unit , datetime.datetime.now() , dp, "Exception"
            logging.error("readMOD.py read: %s" % desc)
            
        else:
            mmc.address = slaveID
            #val  = mmc.read_register(register, 0)
            mmc.debug=False
            
            #test fuer modbus kommunikation...
            val = None
            s = ""
            while retry > 0:
                try:
                    val = mmc.read_float(register, modbusCommand, datalen)
                    if retry < 3:
                        logging.error("Retry %d successful for %s, modbusID  %s" % (3-retry, port, str(modbusID)))
                    if retry < 3:
                        s = "(" + str(3-retry) + ")"

                    retry = 0

                except IOError as e:
                    time.sleep(0.1)
                    retry = retry - 1
                    logging.error ("readMOD.py Modbus got IOError; retry%d! for %s, modbusID  %s,  %s, %s" %(retry, port, str(modbusID), boxtype, parmname))
                    
            if val is None:
                val = mmc.read_float(register, modbusCommand, datalen)
            
                
            rv = (desc,
                 val, unit, 
                 datetime.datetime.now() , 
                 dp, "Ok", s)
                 
                 
            globals.modbusQuality = globals.modbusQuality +1
            if globals.modbusQuality > 100:
                globals.modbusQuality = 100
            
    except Exception as e:
        logging.exception ("readMOD.py: q: %d read_mod_raw got exception for %s, %s, %s, %s" %(globals.modbusQuality, port, str(modbusID), boxtype, parmname))
        rv= desc, 0, unit + "(exc)", datetime.datetime.now() , dp, "Exception"
        #mmc = globals.MODport[port]
        # delete port (probably broken...)
        #mmc.serial.close()
        #del globals.MODport[port]
        globals.modbusQuality = globals.modbusQuality - 10
    finally:
        pass
        #if not mmc is None:
        #    if mmc.serial.isOpen:
        #        logging.error ("readMOD.py: read: make an explicit close on mmc.serial")
        #        mmc.serial.close()

    return rv    
    
#----------------------------------------------------------------------------------------------------
# read takes defined datapoint syntax:
# takes list or string: /port/modID/parmname/boxtype
# parmname is defined as a table in pvOpt.ini
# the communication parameters are defined  per Port in pvOpt.ini
#
# returns list: Name, Value, Unit, timestamp, datapoint ID
#
@logged(logging.DEBUG)
def read(dp):
    #logging.error("MODSEMA-want")
    globals.modbusSema.acquire()
    #logging.error("MODSEMA-have")
    try:
        
        if type(dp) is str:
            dpList=dp.split('/')
        else:
            dpList=dp

        rv = metadata.read("MOD/" + dp)
        # 
        modPort=""
        if len(dpList) > 0:
            modPort=dpList[0]
            
        modID=""
        if len(dpList) > 1:
            modID = dpList[1]
            
        # check if there are definitions for this ID in pvOpt.ini file for the box:port/id definition.
        # globals.hostName
        co=globals.gConfig.__dict__
        k=globals.hostName + ":MOD/" + dpList[0]
        #print ("MOD.read: search in .ini file: ", k)
        if k in co:
            #print ("found ", k)
            if dpList[1] in co[k]:
                #print ("found2 ", dpList[1])
                #print ("MOD.read: Replace ", dpList[1], " by " , co[k][dpList[1]])
                idType = co[k][dpList[1]].split('/')            
                dpList[1]=idType[0]
                dpList.insert(2,idType[1])
                #print ("mod.read: dpList is ", dpList)
                

        if len(dpList) < 4:  # brauche  4 elemente
            logging.error("readMOD.read got no valid datapoint %s" % (dp))
            
            dpList += [""]        
            #rv= "%s" %(dp), 0, "~" , datetime.datetime.now() , "MOD/%s" %("/".join(dpList)), "Exception"
            rv[1]=0
            rv[5]="Exception"
            

        else:
            rv = read_mod_raw(dpList[0], dpList[1], dpList[2], dpList[3], rv)
            
    except Exception as e:
        rv[0] = "readMOD.py: exception %s for %s " % (type(e).__name__, str(dp))
        logging.exception (rv[0])
        rv[5] = "Exception"
        
    finally:
        globals.modbusSema.release()        
        #logging.error("MODSEMA-released")
        
    return rv

#----------------------------------------------------------------------------------------------------
# MAIN:
#
if __name__ == "__main__":
  with config.configClass() as configuration:
#    gConfig=configuration
    globals.config= configuration
    # print list of available parameters.

    while 1:                
        #dps = ["ttyUSB0/1/ZAEHLER/P1Volt"]
        #dps = ["ttyUSB0/ZADAMPF/P1Volt"]
        dps = [
                "ttyUSB.modbus/1/ZAEHLER/P1Power",
                "ttyUSB.modbus/1/ZAEHLER/P2Power",
                "ttyUSB.modbus/1/ZAEHLER/P3Power",
                "ttyUSB.modbus/1/ZAEHLER/SystemPower",
                "ttyUSB.modbus/1/ZAEHLER/ImportWh",
                "ttyUSB.modbus/1/ZAEHLER/ExportWh",

                "ttyUSB.modbus/2/ZAEHLER/P1Power",
                "ttyUSB.modbus/2/ZAEHLER/P2Power",
                "ttyUSB.modbus/2/ZAEHLER/P3Power",
                "ttyUSB.modbus/2/ZAEHLER/SystemPower",
                "ttyUSB.modbus/2/ZAEHLER/ImportWh",
                "ttyUSB.modbus/2/ZAEHLER/ExportWh"
                ]
        dps = [
                "ttyUSB.modbus/18/SDM120/Power",
                "ttyUSB.modbus2/18/SDM120/Power",
                "ttyUSB.irKopf/18/SDM120/Power",
                "ttyUSB.modbus/10/SDM120/Power",
                "ttyUSB.modbus2/10/SDM120/Power",
                "ttyUSB.irKopf/10/SDM120/Power"
                ]

        print ("read  %s" % str(dps))
                
        p = [read(dp) for dp in dps]
            
        try:    
            for pp in p:
                s = "%s: %5.3f %s, %s %s" %(pp[0] , pp[1], pp[2], pp[4], pp[5])
                print (s)
        except:
            print ('exception in main?')
            print (p)

        time.sleep(3)

