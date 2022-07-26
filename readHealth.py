#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#
#  readHealth.py 
#  reads 
#     cpu usage
#     disk free
#     computer uptime
#
#  uses psutils; have to be installed on target box:
#      apt-get install build-essential python-dev python-pip
#      pip install psutil
#      python -c "import psutil"
#
#  apt-get update
#  apt-get install python3-pip
#  pip-3.2 install psutil
#  python3 -c "import psutil"
#
# or see http://www.isendev.com/app/entry/39
#
print ("imported " + __name__)

import os, glob, time, sys, datetime
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged
import metadata
import psutil

#----------------------------------------------------------------------------------------------------
# write:
#
#

@logged(logging.DEBUG)
def write(dp, value, dummy = None):
    rv = ""
    return rv

#----------------------------------------------------------------------------------------------------
# getList:
#   gets a plain list of defined variables
#   dp is a part of the datapoint (e.g. the first part of the datapoints
#
@logged(logging.DEBUG)
def getList(dp):
    rv = ["CPU", "DISK", "RAM", "PROC", "UPTIME", "UPTIMESERVICE"]
    return rv


#----------------------------------------------------------------------------------------------------
#
#   returns number of open filehandles and descriptors
#
logged(logging.DEBUG)
def getFile(which):

    rv = 0

    p = psutil.Process(os.getpid())
    if which == "files":
        rv = p.open_files()
    if which == "desc":
        rv = p.num_fds()
    else:
        rv = -1
    
    return rv
    
#----------------------------------------------------------------------------------------------------
#
#   returns list of processors (PID, NAME, cmdline)
#  filters on whichproc.
#
@logged(logging.DEBUG)
def getProcesses(whichproc):

    rv = ""
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'cmdline'])
        except psutil.NoSuchProcess:
            pass
        else:
            #print (pinfo)
            if whichproc == "" or whichproc.upper() == pinfo["name"].upper():
                rv = rv + "%d=(%s) %s, " % (pinfo["pid"], pinfo["name"], ", ".join(pinfo["cmdline"]))
            
    return rv
#----------------------------------------------------------------------------------------------------
# getCPU():
#   reads the percent usage of the CPU usage
#
@logged(logging.DEBUG)
def getCPU(interv):
    rv = psutil.cpu_percent(interval=interv)
    print ("getCPU returns %5.3f" % rv)
    return rv

#----------------------------------------------------------------------------------------------------
# getUpTime():
#   reads the uptime of computer (time since start of process id 1)
#
@logged(logging.DEBUG)
def _getUpTime(p):

    secs = time.time() - p.create_time()    
    #rv = str(datetime.timedelta(seconds=int(secs)))
    rv = secs
    #strip milliseconds
    #rv = rv.split('.')[1]
    
    #print ("uptime is %s " % str(datetime.timedelta(seconds=int(secs))))  #time.strftime("%Y-%m-%d %H:%M:%S", rv)
    
    return rv

#----------------------------------------------------------------------------------------------------
# getUpTimeService():
#   reads the uptime of computer (time since start of process id 1)
#
@logged(logging.DEBUG)
def getUpTimeService(dummy):
    p = psutil.Process(os.getpid())
    #return "%s sec for process %s" %(str(_getUpTime(p)), str(p))
    return _getUpTime(p)


def getUpTime(dummy1):
    p = psutil.Process(1)
    #return "%s sec for process %s" %(str(_getUpTime(p)), str(p))
    return _getUpTime(p)


    #----------------------------------------------------------------------------------------------------
# getDISKS():
# returns a list of disks currently mounted somewhere.
#
@logged(logging.DEBUG)
def getDISKS():
    disk = psutil.disk_partitions()
    #",".join([x[0]+"="+x[1] for x in disk])

    rv = ",".join([x[1].replace("/",".") for x in disk])    # mountpoints
    # da ich slashes nicht in datenpunkten verwenden kann, nehm ich jetzt punkte:
    
    return rv


#----------------------------------------------------------------------------------------------------
# getDISK():
#   reads the percent usage of the disk.
#
@logged(logging.DEBUG)
def getDISK(what, whichpath):

    rv = 0
    
    whichpath = whichpath.replace(".","/")
        
    if whichpath == "":
        whichpath = "/"
    
    what = what.lower()        
    
    if what == "disks":
        rv = getDISKS()
    else:
        usage=psutil.disk_usage(whichpath)
        # gets something like: 
        #sdiskusage(total=7605489664, used=3376402432, free=3819147264, percent=44.4)
        what = what.lower()

        if what == "total":
            rv = usage.total / 1e6 # in Megabytes
        elif what == "used":
            rv = usage.used  / 1e6
        elif what == "free":
            rv = usage.free  / 1e6
        elif what == "percent":
            rv = usage.percent
        else:
            logging.error("readHealth::getDISK  %s not contained" % what)
    
    return rv, whichpath

#----------------------------------------------------------------------------------------------------
# getRAM():
#   reads the percent usage of the disk.
#
@logged(logging.DEBUG)
def getRAM(whichram):
    if whichram == "":
        whichram = "percent"
        
    ram = psutil.virtual_memory()
    print ("ram got ", ram)
    
    rv = 0
    # ram is a svmem class:
    #svmem(total=455712768, available=404623360, percent=11.2, used=116613120, free=339099648, active=75726848,    
    #      inactive=22532096, buffers=19783680, cached=45740032)
    whichram=whichram.lower()
    if whichram == "percent":
        rv = ram.percent
    elif whichram == "total":
        rv = ram.total / 1e6 # in Megabytes
    elif whichram == "available":
        rv = ram.available / 1e6 # in Megabytes
    elif whichram == "used":
        rv = ram.used / 1e6 # in Megabytes
    elif whichram == "free":
        rv = ram.free / 1e6 # in Megabytes
    elif whichram == "active":
        rv = ram.active / 1e6 # in Megabytes
    elif whichram == "inactive":
        rv = ram.inactive / 1e6 # in Megabytes
    elif whichram == "buffers":
        rv = ram.buffers / 1e6 # in Megabytes
    elif whichram == "cached":
        rv = ram.cached / 1e6 # in Megabytes
    else:
        logging.error("readHealth::getRAM psutil returned wrong structure %s not contained" % whichram)
    
    return rv


#----------------------------------------------------------------------------------------------------
# read:
#   reads a variable from globals.var dictionary
#
@logged(logging.DEBUG)
def read(dp):

    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp

    rv = metadata.read("HEALTH/" + dp.upper(), "HEALTH/" + dp.upper())

    try:        
        if dp is None:
            logging.error("readHealth.read got no datapoint.")
        elif "" == dp:
            logging.error("readHealth.read got empty datapoint.")
        
        what="CPU"
        what1=""
        what2=""
        if len(dpList) > 0:
            what=dpList[0]
        if len(dpList) > 1:
            what1=dpList[1]
        if len(dpList) > 2:
            what2=dpList[2]
            
        rv[5] = "Ok"
        
       
        
        if what == "CPU":
            i=int(what1)
            if i == 0:
                i=10
            result = getCPU(i)
        elif what == "DISK":
            result, whichpath = getDISK(what1, what2)
            rv[0]= rv[0] + " " + whichpath
        elif what == "UPTIME":
            result = getUpTime(what1)
        elif what == "UPTIMESERVICE":
            result = getUpTimeService(what1)
        elif what == "RAM":
            result = getRAM(what1)
        elif what == "PROC":
            result = getProcesses(what1)
        elif what == "FILE":
            result = getFile(what1)
        else:
            raise ValueError('readHealth.read got unknown datapoint %s ' % (dp))
            result = 0
            rv[5] = "Exception"
            
        rv[1] = result
        
    except Exception as e:
        rv = "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now(), dp, "Exception"
        logging.exception("readHealth.py")
            
        
    return rv
    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
#-------------------------------------------------------------------------
#
#
def main():

    with config.configClass() as configuration:
        globals.config= configuration   
        print ("readhealth  start - with - debug")
        logging.getLogger().setLevel(logging.DEBUG)
        #rv = read ("CPU")
        #print ("got CPU usage: ", rv)
        
        if True:        
            rv = read ("DISK/DISKS")
            s = "%s: %s %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
            print (s)
            
            mountpoints=rv[1].split(",")
            for path in mountpoints:
            
                rv = read ("DISK/percent/" + path)
                s = "%s: %5.3f %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
                print (s)

                rv = read ("DISK/USED/" + path)
                s = "%s: %5.3f %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
                print (s)
                
                rv = read ("DISK/FREE/" + path)
                s = "%s: %5.3f %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
                print (s)
                
                rv = read ("DISK/total/" + path)
                s = "%s: %5.3f %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
                print (s)
                
                print ("-----------------------------------")
        
        if False:        
            rv = read ("CPU/10")
            s = "%s: %5.3f %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
            print (s)

        if False:        
            rv = read ("RAM/percent")
            s = "%s: %5.3f %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
            print (s)
    
            rv = read ("RAM/FREE")
            s = "%s: %5.3f %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
            print (s)
            
            rv = read ("RAM/percent")
            s = "%s: %5.3f %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
            print (s)

        if False:
            rv = read ("PROC/main.py")
            s = "%s: %s %s, %s" %(rv[0] , rv[1], rv[2], rv[4])
            print (s)

        if True:
            rv = read ("UPTIMESERVICE/R")
            s = "%s: %s %s, %s, %s" %(rv[0] , rv[1], rv[2], rv[3], rv[4])
            print (s)
            rv = read ("UPTIME")
            s = "%s: %s %s, %s, %s" %(rv[0] , rv[1], rv[2], rv[3], rv[4])
            print (s)
        
        if False:
            rv = getList("")
            print ("Got list of health- values: ", rv)
                
        
        
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()
