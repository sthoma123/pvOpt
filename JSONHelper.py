#!/usr/bin/python3

import re
import json
import datetime
import time
import urllib.parse
import logging 
from funcLog import logged

DATE_FORMAT_milli="%Y-%m-%d %H:%M:%S.%f"
DATE_FORMAT="%Y-%m-%d %H:%M:%S"

#-----------------------------------------------------------------
#
#
def JSON2pyDateTime(s, dateformat):
    print ("JSON2pyDateTime got " + s + " treat like " + dateformat)
    s=s.replace("T", " ") # to solve the separator rpoblem (always use " ")
    s=s.replace(",", ".") #
    offset = datetime.timedelta(hours=0)
    if s[-1] == "Z":      # Z-time... remove trailing "Z" and adjust to localtime
        now_timestamp = time.time()
        offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
        s=s[:-1]
    #print ("decodeParm recognizes dtetime")
    rv =  datetime.datetime.strptime(s, dateformat)
    rv = rv + offset #offset is timedelta datetime.timedelta(hours = offset)
    print ("JSON2pyDateTime returned " + str(rv))
    
    return rv
 

#from http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime
def utc2local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

    
@logged(logging.DEBUG)
def JSONDateTimeHandler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat("T")  # old firefox requires a "T" as separator (hope it is Ok for all other readers
    else:
        print ('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))
        logging.error ('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))

        
@logged(logging.DEBUG)
def JSONdatetime_parser(obj):

    rv = None
    
    #print ("JSONdatetime_parser -1 ", obj, str(type(obj)))
    
    if type(obj) is list or type(obj) is tuple:
        rv = list()
        for v in obj:
            rv.append(JSONdatetime_parser(v))
    
    elif type(obj) is dict:
        rv=dict()
        for k, v in obj.items():
            #print("JSONdatetime_parser: ", k, v)                
            rv[k] = JSONdatetime_parser(v)    
    elif type(obj) is str:
        x=obj.replace("T", " ") # to solve the separator rpoblem (always use " ")
        x=x.replace(",", ".") #
        #print ("parser: str ", obj)
        if re.search("\d{4,4}-\d\d-\d\d\D\d\d:\d\d:\d\d\.\d+", x):
            try:
                rv = datetime.datetime.strptime(x, DATE_FORMAT_milli)
            except:
                rv = "unknown datetimeformat: " + x
        elif re.search("\d{4,4}-\d\d-\d\d\D\d\d:\d\d:\d\d", x):            
            try:
                rv = datetime.datetime.strptime(x, DATE_FORMAT)
            except:
                rv = "unknown datetimeformat: " + x
        else:
            rv = obj
    else:
        rv = obj
                        
                        
    return rv
    
#------------------------------------------------------
# encodeParm
#
# wasauch immer als parm daherkommt wird als String fuer eine URL aufbereitet.
#
# currently string, int, float and date are supported.
#
@logged(logging.DEBUG)
def encodeParm(parm):

    rv = _encode(parm)

    return urllib.parse.quote(rv)
    
#------------------------------------------------------
# encodeParm
#
# wasauch immer als parm daherkommt wird als String aufbereitet.
#
# currently string, int, float and date are supported.
#
@logged(logging.DEBUG)
def _encode(parm):

    rv = ""
    
    if type(parm) is int:
        rv=str(parm)
    elif type(parm) is float:
        rv=str(parm)    
    elif type (parm) is str:
        rv=parm    
    elif type(parm) is datetime.datetime:
        rv=parm.isoformat("T")    # old firefox requires a "T" as separator (hope it is Ok for all other readers
    else:
        rv =json.dumps(parm, default=JSONDateTimeHandler)   
    
    return rv        

#------------------------------------------------------
# decode
#
# kriege irgendetwas als String
# currently string, int, float and date are supported.
#

@logged(logging.DEBUG)
def _decode(s):
    rv=None
    #print ("decodeParm gets ", s)

    if type(s) is str:        
        if len(s)>0:
            try:
                if  re.search("\A-*\d+[.]\d*\Z", s):   #float  
                    #print ("decodeParm recognizes float")
                    rv=float(s)
                    
                elif re.search("\A[-+]?\d+\Z", s):   #int
                    #print ("decodeParm recognizes int")
                    rv=int(s)
                    
                elif re.search("\A\d{4,4}-\d\d-\d\d\D\d\d:\d\d:\d\d\Z", s):
                    rv = JSON2pyDateTime(s, DATE_FORMAT)

                elif re.search("\A\d{4,4}-\d\d-\d\d\D\d\d:\d\d:\d\d(\.\d+)?Z?\Z", s):
                    rv = JSON2pyDateTime(s, DATE_FORMAT_milli)
                   
                elif re.search("\A[\[{(].+[])}]\Z", s):  # json objekte: list/tuple/dict 
                    #print ("match date")
                    #print ("decodeParm recognizes JSON")
                    #print ("decodeParm JSON1: ", s, str(type(s)))
                    rv = json.loads(s)
                    #print ("decodeParm JSON2: ", rv, str(type(rv)))
                    rv = JSONdatetime_parser(rv)
                    #print ("decodeParm JSON3: ", rv, str(type(rv)))
                else:
                    #print ("decodeParm recognizes nothing, durchschleifen")
                    rv = s
            except:
                logging.exception("decodeParm has problems with %s", s)

    #print("_decode returning %s" % str(rv))
    
    return rv
      

#------------------------------------------------------
# decodeParm
#
# kriege irgendetwas als String (gequotet)
# currently string, int, float and date are supported.
#

@logged(logging.DEBUG)
def decodeParm(parm):


    rv=None
    #print ("decodeParm gets ", parm)

    if type(parm) is str:
        s = urllib.parse.unquote(parm)
        #strip unnecessary double quotes (coming from javascript)
        if len(s)>0:
            if s[0]=="\"":
                s = s[1:]
            if s[-1]=="\"":
                s = s[:-1]        
            rv = _decode(s)
        
    #print ("decodeParm returns ", rv)
        
    return rv

    
