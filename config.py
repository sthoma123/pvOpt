#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging

# handles static and site specific cofiguration.
# this is a kind of overlay, every change comes into the site specifi configuration (.ini file)
# for a read, static and site specifics are merged. 
# for deletes, a stub has to be created? parent is copied?.
#

print ("imported " + __name__)

import os, glob, time, sys, datetime
import json
import JSONHelper
import configparser
import optparse
import parser
from collections import ChainMap
import logging
from funcLog import logged
import copy

###default loggin to console, before I got a filename:
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()  # create console handler 
ch.setLevel(logging.WARNING)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)
###default loggin to console, before I got a filename:
            


# set theh following variable to True if you don't want me to grab the arguments
doNotParseCommandline = False
#print("config.py sets doNotParse to False!")

LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}
                  
def createPID(pidfile):
#/usr/bin/env python

    pid = str(os.getpid())

    if os.path.isfile(pidfile):
        logging.error("%s already exists, deleting" % pidfile)
        #sys.exit()
        os.unlink(pidfile)
        
    f=open(pidfile, 'w')
    f.write(pid)
    f.close()

#------------------------------------------------------------------------------------
#  
# cconverts all JSON sub elements into their native type
# needed for dictionaries in elements
#
#
JSONPREFIX = "JSON:"
lenPREFIX=len(JSONPREFIX)

def translateFromINI(c):
    assert type(c) is dict or type(c) is configparser.SectionProxy, "translateFromINI expect a dict or configparser.SectionProxy, got a %s " % (str(type(c)))
    
    rv = {}
    for key in c:
        try:
            content=c[key]
            assert type(content) is str and len(content)> 0, "expecting string content in key %s (got %s)"%(key, str(type(content)))
            if content[0:lenPREFIX] == JSONPREFIX:
                data = JSONHelper._decode(content[lenPREFIX:])
                rv[key] = data
            else:
                rv[key] = content
        except Exception as e:
            s="in %s" %(key)
            print (s)
            raise type(e)(s) from e   #weiterwerfen...

    #print("translateFromINI returns %s " % (str(rv)))
    
    return rv
    
    
#------------------------------------------------------------------------------------
#  gets a dict and converts all lower level dicts to JSON
#
#
def translateToINI(c):
    assert type(c) is list or type(c) is dict, "translateToIni expect a dict or list, got a %s " % (str(type(c)))
    
    rv = {}
    
    if type(c) is dict:
        for key in c:
            data = c[key]
            td = type(data)
            #print ("toIni: got %s %s" % (str(td), data))
            
            if td is dict or td is list or td is tuple or td is datetime.datetime:
                jData = JSONHelper._encode(data)
                rv[key] = JSONPREFIX + jData
            else:
                rv[key] = data
    elif type(c) is list:
        jData = JSONHelper._encode(c)
        rv = JSONPREFIX + jData
    else:
        print ("translateToINI got unknown type %s?" %(str(type(c))))
        rv = c
            
    #print ("TranslateToIni returns %s" % str(rv))

    return rv
    
#------------------------------------------------------------------------------------
def writeConfigFile(changedConfig, configfilename):

    rv = ""
    print("ChangedConfig is: -------------------------------------")
    printDict(changedConfig)
    
    if changedConfig is None:  # could be if global config file is not altered
        changedConfig={"dummy" : "None"}
        
    try:
        conf = configparser.ConfigParser(allow_no_value=True, interpolation=None)  #.replace('%', '%%')
        conf.optionxform = lambda option: option   #otherwise names will be transformed to lowercase.
        main = {}
        for key in changedConfig.keys():
            c = changedConfig[key]
            if type(c) is dict:
                conf[key] = translateToINI(c)
            elif type(c) is list:
                main[key] = translateToINI(c)
            else:
                main[key] = c
                
        conf["main"] = main
        
        with open(configfilename, 'w') as configfile:
           conf.write(configfile)
           
        rv = "writeConfigFile %s Ok" % (configfilename)
        
    except Exception as e:
        rv="exception during write to site specific config file %s : %s" %(configfilename, str(e))
        logging.exception("creation of config object %s " % configfilename)
    pass
    
    return rv
    

#------------------------------------------------------------------------------------
def readConfigFile(configfilename):
    
    print("Init: readConfigFile: %s" % configfilename)
    
    rv = dict()
    conf = configparser.ConfigParser(allow_no_value=True, interpolation=None)
    conf.optionxform = lambda option: option   #otherwise names will be transformed to lowercase.
    if len(conf.read(configfilename)) == 0:
        s="ini file not found: >%s<" % configfilename
        print (s)
        logging.error(s)
    else:
        if "main" not in conf:
            s="No [main] in " + configfilename
            print (s)
            logging.error(s)
        else:   
            rv.update(dict(conf["main"]))
        
        for ke in conf.sections():
            if ke != "main":
                rv.update({ke : dict()})
                try:
                    rv[ke].update(translateFromINI(conf[ke]))
                except Exception as e:
                    s=" in section %s" %(ke)
                    print (s)
                    raise type(e)(s) from e  #weiterwerfen...
                    
        # obsolete method: check if there are json strings: decode them
        # json identifier by in value.

        lists={}
        for var in rv.keys():
          if var[0:5] == "json_":
            lists.update({var[5:]: json.loads(rv[var])})
        rv.update(lists)
    
    return rv

    
#--------------------------------------------------------------------------------
#
#  returns a - b that means returns everything has is only in b or has changed in b
#  lists are treated separately ("add" and "delete" applies)
#   warning: dict is not copied; only reference is set with equation!
#

def diff(a,b, path=None):
    
    rv = copy.copy(b) #not deepcopy, since every level is treated on it's own. other types are Ok for .copy
    if path is None: path = []

    if type(rv)==type(a): # otherwise new anyway.
        if isinstance(a, dict):
            for key in a:
                if key not in rv:
                    rv[key] = "deleted"
                else:
                    rv[key]=diff(a[key], rv[key], path + [str(key)])
                    if rv[key] is  None:
                        rv.pop(key)
            if len(rv) == 0:
                rv = None
                
        elif isinstance(rv, list):
            empty=True
            for index, val in enumerate(a):
                if index < len(rv):
                    d = diff(val, rv[index], path + [str(index)])
                    if d is not None:
                        empty=False
                    rv[index]=d
                else:
                    rv.append("deleted")
                
            if (len(rv) == len(a)) and empty:
                rv = None
            #rv = None #to be done!!!
            
        elif isinstance(rv, str):
            if rv == a:
                rv = None
                
        elif isinstance(rv, int):
            if rv == a:
                rv = None
                
        else:
            if rv == a:
                rv == None

    if False:
        print ("diff--------------------------------------------------------------------")
        print ("a:")
        printDict(a)
        
        print ("b: --------------------------")
        printDict(b)
        
        print ("returns: --------------------------")
        printDict(rv)
            
    return rv
            
#--------------------------------------------------------------------------------------------
#
#
#
#--------------------------------------------------------------------------------------------
def mergeWorker(a,b, key, path):

    if key == "add": # I suppose: a should be a list: enforce! (otherwise .add is nonsense)
        if not isinstance(a, list):
            print ("Merge#add: make target to List path %s (was %s with len %d)" % (".".join(path + [str(key)]), 
                str(type(a)), len(a)))
            a = []

        a.append(b[key])
        #print ("Merge: added to a: %s

    elif key == "delete":
        k = b[key]
        if isinstance(a, list):
            try:
                del a[int(k)]  #element could be missing or k is not an integer
            except Exception as e:
                s="merge: path %s cannot delete %s element from list %s (len %s)" %(".".join(path + [str(key)]), str(k), 
                        str(type(a)), len(a))
                logging.exception(s)
                raise RuntimeError("%s %s" % (s, str(e)) ) # forward exception
                
        elif isinstance(a, dict): #delete from dict
            try:
                del a[k]  #element in a dict
            except Exception as e:
                s="merge: path %s cannot delete %s element from dict %s (len %s)" %(".".join(path + [str(key)]), str(k), 
                        str(type(a)), len(a))
                logging.exception(s)
                raise RuntimeError("%s %s" % (s, str(e)) ) # forward exception
        else: #not a dict and not a list (what else?)
            s="merge, delete: unknown type in target path %s cannot delete %s element from %s (len %s)" %(".".join(path + [str(key)]), str(k), 
                        str(type(a)), len(a))
            logging.exception(s)
            raise RuntimeError("%s %s" % (s, str(e)) ) # forward exception
    else:  #key is not add or delete
        keyA = key
        keyB = key
        if isinstance(a, list):
            if not isinstance(key,int):
            # key for a has to be numeric
                if str.isnumeric(key): 
                    keyA = int(key)
                else:
                    raise Exception('Conflict at %s try to merge into list without index %s' % (path, key))
            
            while len(a) <= keyA:  #both zero based
                a.append(None)   #fill
                
        elif isinstance(a, dict):
            if not keyA in a:
                a[keyA] = None      #to avoid exception during merge recursion below
        else:
            ###import web_pdb; web_pdb.set_trace() #debugging
            
            raise Exception("merge at %s: a has wronge type %s (should be list or dict) at key %s" % (path, str(type(a)), key))
            
                
        if isinstance(b, list) and not isinstance(key,int):
            if str.isnumeric(key): 
                keyB = int(key)
            else:
                raise Exception('Conflict at %s try to merge from list without index %s' % (path, key))
            
            # for b it's Ok if it's a string (coming from hash syntax) or an int
            # vielleicht hier nicht in die nächste Ebene!
            #
            
        #import web_pdb; web_pdb.set_trace() #debugging
        #if isinstance(b[keyB], dict):
        #if (not keyA in a) or isinstance(a[keyA],list) or (not isinstance(a[keyA], dict)): #does not fit ...
            #print ("created empty %s " % str(keyA));
        #    a[keyA]= b[keyB]  #copy.deepcopy(
        #else:
        a[keyA] = merge(a[keyA], b[keyB], path + [str(key)])
                
    return a

#--------------------------------------------------------------------------------------------
#
#
# some special handling: b wins always
# keys are separated by "#" to access subitems
# list items are accessed by index
# delete and add are special keys.
# deep merge a dictionary.
#
#--------------------------------------------------------------------------------------------
#
def merge(a, b, path=None):
    
    #"merges b into a"
    if path is None: path = []
    
    #expand keypaths of newly added dict (separated by "#")
    if isinstance(b, dict):
        for key in b:
            keyList = key.split("#")
            if len(keyList) > 1:
                b[keyList[0]]={"#".join(keyList[1:]) : b[key]}  #move content one level deeper
                b.pop(key, None)
                #print ("merge: expanded key %s to %s "%(key, str(b)))
                
    #iterate either over dict or over list
    if isinstance(b, list):
        if a is None:
            a=[]
        for key, val in enumerate(b):
            a=mergeWorker(a,b,key, path)
    elif isinstance(b, dict):
        if a is None:
            a={}
        for key in b:
            a=mergeWorker(a,b,key, path)
    else: #no iteration possible:
        if b == "deleted":
            a = None
        elif b is not None:  # a might be None (new) or overwritten
            a = b
        #else:
        #  b is None, do nothing, leave a

    return a


#-----------------------------------------------------------------------------------------
#
# global configuration is written into config dict, 
# config is merged with siteconfig into configMap
# all write operations to the config go into configMap, 
# flushConfig makes a diff siteconfig-configmap and writes ist into siteSpecific config file.
# lists handling: merge copies empty list elements marks deleted with "deleted" and add new after a special list element "add"
# ChainMap is no longer used;
#
class configClass:
    def __init__(self):        
        self.configfilename='/etc/pvOpt.ini'
        #self.configs={} 
        self.config = {}
        self.configMap={}

        try:
            self.config.update(self.readConfiguration(self.configfilename))

            self.siteConfigFileName = self.config["siteConfigFile"]
            self.siteConfig={}
            if self.siteConfigFileName != "":
                self.siteConfig.update(self.readConfiguration(self.siteConfigFileName))
                
            self.configMap = merge(copy.deepcopy(self.config), self.siteConfig)
            
            if not doNotParseCommandline:                
                #commmandline overrides configfile (for debuglevels etc.)
                parser = optparse.OptionParser()
                parser.add_option('-l', '--logging-level', help='Logging level, e.g. debug, warning, info, error, critical')
                parser.add_option('-f', '--logging-file', help='Logging file name, e.g. /var/log/pvOpt.log')
                
                (options, args) = parser.parse_args()
                
                if type(options.logging_file) is str and options.logging_file != "" :
                    self.configMap["logfilename"]=options.logging_file
                    print ("config: options say: setting logfile to ", self.configMap["logfilename"])
                    
                if not options.logging_level is None:
                    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
                    if logging_level == 0:
                        print ("wrong logging level: %s " % (options.logging_level))
                    else:
                        self.configMap["debugLevel"] = logging_level
                
            #if "debugLevel" in self.configMap:
            #        print ("logging with level ", self.configMap["debugLevel"])            
                
            #if "logfilename" in self.configMap:
            #    print ("logging to logfilename ", self.configMap["logfilename"])
                
        except Exception as e:
            print ("exception during creation of config object %s: %s" %(self.configfilename, str(e)))
            logging.exception("creation of config object")
            
        
        # ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        try:
            if "logfilename" in self.configMap: 
                #if somebody already called logging.error, there is a root streaming handler (which seem to log to the console)
                #therefore just add a file handler
                logger = logging.getLogger()                
                ch = logging.FileHandler(filename=self.configMap["logfilename"])
                #print ("config: set logFilename to ", str(self.configMap["logfilename"]))
                #ch = logging.handlers.WatchedFileHandler(filename=self.configMap["logfilename"])                
                ch.setLevel(logging.DEBUG)

                formatter = logging.Formatter('%(asctime)s-%(threadName)s-%(name)s-%(levelname)s-%(message)s')
                ch.setFormatter(formatter)

                logger.addHandler(ch)
            else:
                s="config: no logfilename in self.configMap"
                logging.error(s)
                
            if "debugLevel" in self.configMap: 
                #print ("config: set loglevel to ", str(logging.getLevelName(int(self.configMap["debugLevel"]))))
                logging.getLogger().setLevel(int(self.configMap["debugLevel"])) 
            else:
                s="config: no debugLevel (Loglevel) in self.configMap"
                logging.error(s)
                
        except Exception as e:
            print ("unable to log to %s: %s" %(self.configMap["logfilename"], str(e)))
            
        s="notAnError: log to %s LogLevel %s started" % (self.configMap["logfilename"], str(logging.getLevelName(int(self.configMap["debugLevel"]))))
        logging.error(s)


    def __enter__(self):
        pass
        return self

    #  

    def __exit__(self, type, value, traceback):
        pass

    #----------------------------------------------------------------------------------------------------
    # reads configfilename and all subsequent includes and returns a merged dict
    #
    def readConfiguration(self, configfilename):
        rv = {}
        includes = configfilename
        while includes != "":
            fileNames = includes.split(",")
            includes = ""
            for fn in fileNames:
                if fn != "":
                    name=fn.strip()
                    confData=readConfigFile(name)
                    if "include" in confData:
                        includes += "," + confData["include"]
                    rv = merge(rv, confData)
                    #print ("merge %s with %s" % (str(rv), str(confData)))
                    
        #print ("readConfiguration returns >>%s<<"% str(rv))            
        return rv
    #----------------------------------------------------------------------------------------------------
    # public:
    def readConfig(self, dp):
        rv = dict()
        if type(dp) is str:
            dp = [dp]
        
        for key in dp:
            rv[key]=self.read1Config(key)
        
        return rv

    #----------------------------------------------------------------------------------------------------
    # section/value
    #
    listOfReservedKeys=["delete", "add"]
    
    def read1Config(self, key):
        rv = None
        l=key.split("#")  # separator hash weil das in .ini files nicht vorkommen sollte
        if l[-1] in self.listOfReservedKeys:
            l=l[0:-1]
        #co=self.__dict__
        co=self.configMap

        while len(l)> 0:
            k = l[0]
            if k != "":
                if isinstance(co, list):
                    try:
                        k = int(l[0]) # has to be an index
                    except:  #obviousely not an integer; will not be Ok when acccessing the list:
                        logging.error("read1Cofig: unknown config for List %s; should be integer" % "#".join(l))
                        pass
                co = co[k]
                if len(l)==1:   # end of iteration...
                    rv = co
                del l[0]
            else:
                if rv is None:
                    #ganze liste als dict zurückgeben
                    if type(co) in [dict, ChainMap]:
                        rv = dict(co)
                    elif type(co) in [list, str, int]:
                        rv = co
                        
                if rv is None:
                    logging.error("read1Config unknown config: %s" % "#".join(l))
                    
                break
                
        #print ("read1config for %s returned %s " % (str(key), str(rv)))
        return rv

    #----------------------------------------------------------------------------------------------------
    #  Flush
    #
    #----------------------------------------------------------------------------------------------------
    def flushConfig(self):
        #printDict(self.configMap, 0)
        d=diff(self.config, self.configMap)
        printDict(d)
        rv = writeConfigFile(d, self.siteConfigFileName)
        print("config written to %s " % (self.siteConfigFileName))
        return rv
        

    #----------------------------------------------------------------------------------------------------
    # data is dict of key/values.
    # keys koennen in der ersten Ebene mit # auf subkeys verweisen.
    #
    # returns value of given datapoint (section)
    #            raise RuntimeError("exec: readConfig for nonexisting dp %s not possible" % dp)

    def writeConfig(self, section, data):
        assert type(data) is dict, "writeConfig got unknown datatype %s; %s expected dict" % (str(type(data)), str(data))
        
        rv = ""
        
        #import web_pdb; web_pdb.set_trace() #debugging
        if section is None or section == "":  #main section
            self.configMap = merge(self.configMap, data)
        else:
            self.configMap = merge(self.configMap, {section : data})
        
        #data contains a whole dictionary. that means that we do not have a single datapoint at this level.
        #therefore I cannot return the content of the given datapoint (I would have to return the whole section)
        #it has to be handled on a higher level (calling function).
        # simply return an empty string, error handling is done by exception.
        
        return rv

    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
#-------------------------------------------------------------------------
#

def printDict(inDict, level=0):

    #print ("got indict ", inDict, inDict.keys, level)
    
    if not isinstance(inDict, dict):
        print ("(%s) %s"%(str(type(inDict)), str(inDict)))
    else:
        for key in inDict.keys():
            sys.stdout.write("-" * (1+level)) # Ausgabe
            sys.stdout.write("%s" % key)
            if type(inDict[key]) is dict:
                sys.stdout.write("\r\n")
                printDict(inDict[key], level + 1)
            else:
                data = inDict[key] 
                ty = str(type(data))
                sys.stdout.write(" (%s) %s:" %( ty, "." * (60-level-len(key)-len(ty))))
                if type(data) is str:
                    s= data
                else:
                    s=str(inDict[key])
                    
                sys.stdout.write(s)
                sys.stdout.write("\r\n")
                
def debugPrintLoggers():
    for k,v in  logging.Logger.manager.loggerDict.items()  :
        print('+ [%s] {%s} ' % (str.ljust( k, 20)  , str(v.__class__)[8:-2]) ) 
        if not isinstance(v, logging.PlaceHolder):
            for h in v.handlers:
                print('     +++',str(h.__class__)[8:-2] )
#
def main(): 

    with configClass() as configuration:
    
        if True:
            debugPrintLoggers()

        if False:
            configuration.writeConfig("schnucki", {"da":"da", "db":"db", "dc":"dc", "LIST":[1,2,3,4,5,6]})
            print("configmap-------------------------------------------")
            printDict(configuration.configMap)
            print("config----------------------------------------------")
            printDict(configuration.config)
            
            configuration.flushConfig()
        

        if False:
            a={"aa":"GEAENDERTdas ist aa", "cc":"dcs ist cc","bb":"GLEICHdbs ist bb",
                    "dd":{"da":"da", "db":"db", "dc":"dc", "LIST":[1,2,3,4,5,6], "OTHERLIST":[1,2,3]}}
            b={"aa":"GEAENDERTdas ist ab", "bb":"GLEICHdbs ist bb",
                    "dd":{"da":"da", "db":"db", "dc":"dceGEAENDERT", "LIST":[1,2,3,4,6,7,8,9,"letztes"], "OTHERLIST":[1,2,3]}}
            print("dictionary a---------------------");
            printDict (a)
            
            print("dictionary b--------------------");
            printDict (b)
            #import web_pdb; web_pdb.set_trace() #debugging
            print("difference:----------------------");
            dif=diff(a,b)
            printDict(dif)
            
            print ("")
            print("dictionary a after diff---------------------");
            printDict (a)
            
            print ("")
            print("merge difference into a -should be b -------------------");
            #import web_pdb; web_pdb.set_trace() #debugging
            d = merge(a,dif)
            printDict (d)

            
        if False:
            print ("config has:")
            #printDict(configuration.__dict__, 0)
            printDict(configuration.configMap, 0)
            x = configuration.readConfig (["MOD/ttyUSB0","currentTimestamp", "homematic"])
            print ("readConfig returned %s " % str(x))
            configuration.writeConfig("testSection", {"currentTimestamp": str(datetime.datetime.now())})
            configuration.writeConfig("testSection", {"testoption": {"A":1, "B":2, "C":3, "testDict":{"aa":1, "bb":2, "cc":3}}})
            configuration.writeConfig("testSection", {"testoption": {"E":42}})
            
            configuration.writeConfig("testSection", {"testListoption": [1,2,{"thirdKeydict":3},4]})

            
            #configuration.writeConfig("testSection", {"testListoption#2": 27})      #set second entry to 27
            configuration.writeConfig("testSection", {"testListoption#add": 28})    #add entry at the end
            print ("after add: testListOption is  %s " % str(configuration.readConfig (["testSection#testListoption"])))
            printDict(configuration.configMap["testSection"], 0)

            configuration.writeConfig("testSection", {"testListoption#delete": 2})  #removes second entry
            print ("after delete: testListOption is  %s " % str(configuration.readConfig (["testSection#testListoption"])))
            
            configuration.writeConfig("testSection", {"testoption#F#numberFIs": 43}) # config by deep path
            configuration.writeConfig("testSection", {"testoption#deep#non#existing#key#is": "verydeeptext"}) # config by deep path
            
             
            x = configuration.readConfig (["testSection#testoption#A", "testSection#testoption#testDict"])
            print ("writeConfig / readConfig returned %s " % str(x))
            configuration.flushConfig()
                
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()
    