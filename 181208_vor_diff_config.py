#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging

# handles static and site specific cofiguration.
# this is a kind of overlay, every change comes into the site specifi configuration (.ini file)
# for a read, static and site specifics are merged. 
# for deletes, a stub has to be created? parent is copied?.
#


import os, glob, time, sys, datetime
import json
import JSONHelper
import configparser
import optparse
import parser
from collections import ChainMap
import logging
from funcLog import logged



# set theh following variable to True if you don't want me to grab the arguments
doNotParseCommandline = False
#print("config.py sets doNotPars to False!")

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
        if c[key][0:lenPREFIX] == JSONPREFIX:
            data = JSONHelper._decode(c[key][lenPREFIX:])
            rv[key] = data
        else:
            rv[key] = c[key]
            
    #print("translateFromINI returns %s " % (str(rv)))
    
    return rv
    
    
#------------------------------------------------------------------------------------
#  gets a dict and converts all lower level dicts to JSON
#
#
def translateToINI(c):
    assert type(c) is list or type(c) is dict, "translateToIni expect a dict or list, got a %s " % (str(type(c)))
    
    rv = {}
    
    for key in c:
        data = c[key]
        td = type(data)
        #print ("toIni: got %s %s" % (str(td), data))
        
        if td is dict or td is list or td is tuple or td is datetime.datetime:
            jData = JSONHelper._encode(data)
            rv[key] = JSONPREFIX + jData
        else:
            rv[key] = data
            
    #print ("TranslateToIni returns %s" % str(rv))

    return rv
    
#------------------------------------------------------------------------------------
def writeConfigFile(changedConfig, configfilename):

    rv = ""
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
                rv[ke].update(translateFromINI(conf[ke]))

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
#
def diff(a,b, path=None):


    return b
# some special handling: b wins always
# keys are separated by "#" to access subitems
# list items are accessed by index
# delete and add are special keys.
# deep merge a dictionary.
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
    
    for key in b:
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
                s="merge: unknown type in target path %s cannot delete %s element from %s (len %s)" %(".".join(path + [str(key)]), str(k), 
                            str(type(a)), len(a))
                logging.exception(s)
                raise RuntimeError("%s %s" % (s, str(e)) ) # forward exception
        else:  #key is not add or delete
            if isinstance(b[key], dict):
                if not key in a or not (isinstance(a[key],list) or isinstance(a[key], dict)):
                    a[key]={}
                a[key] = merge(a[key], b[key], path + [str(key)])
            elif isinstance(b[key], list):
                #if not key in a or not isinstance(a[key],list):  #initialisieren, wenn addiert.
                #    a[key]=[]  #new list
                #a[key].extend(b[key])  # extend ist nicht gut, wenn ich flushConfig mache, verdoppelt sich die Liste.
                # key sollte ein integer sein:
                a[key] = b[key]
            else:  #b[key] is basic type, literal, integer etc.
                if key in a:
                    print ("overwritten %s (is a conflict?)"% '.'.join(path + [str(key)]))
                if isinstance(a, list): # numerisch indiziert
                    a[int(key)] = b[key] #b itself is still a dict, therefore index is not numeric...
                else:
                    a[key] = b[key]
                #raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
    return a


class configClass:
    def __init__(self):        
        self.configfilename='/etc/pvOpt.ini'
        self.siteConfig = {}  # all write operations to the config go into changedConfig, in the end, this is written to user.ini
        #self.configs={} #enthaelt die daten fuer configMap getrennt nach .ini files. (user, site, global, oder wie mit include konfiguriert)
        self.config = {}
        self.configMap=ChainMap(self.siteConfig, self.config) #alle zugriffe gehen ueber configMap

        try:
            self.config.update(self.readConfiguration(self.configfilename))
            self.siteConfigFileName = self.config["siteConfigFile"]
            if self.siteConfigFileName != "":
                self.siteConfig.update(self.readConfiguration(self.siteConfigFileName))
            
            if not doNotParseCommandline:                
                #commmandline overrides configfile (for debuglevels etc.)
                parser = optparse.OptionParser()
                parser.add_option('-l', '--logging-level', help='Logging level, e.g. debug, warning, info, error, critical')
                parser.add_option('-f', '--logging-file', help='Logging file name, e.g. /var/log/pvOpt.log')
                
                (options, args) = parser.parse_args()
                
                if type(options.logging_file) is str and options.logging_file != "" :
                    self.configMap["logfilename"]=options.logging_file
                    #print ("config: setting lofile to ", self.configMap["logfilename"])
                    
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
#                logging.basicConfig(filename=self.configMap["logfilename"],level=int(self.configMap["debugLevel"]), format='%(asctime)s--%(threadName)s-%(name)s--%(levelname)s--%(message)s')
                #print ("config: basicConfig set filename to ", str(self.configMap["logfilename"]))
                logging.basicConfig(filename=self.configMap["logfilename"],format='%(asctime)s--%(threadName)s-%(name)s--%(levelname)s--%(message)s')
            if "debugLevel" in self.configMap: 
                #print ("config: set loglevel to ", str(logging.getLevelName(int(self.configMap["debugLevel"]))))
                logging.getLogger().setLevel(int(self.configMap["debugLevel"])) 
        except Exception as e:
            print ("unable to log to %s: %s" %(self.configMap["logfilename"], str(e)))

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
        rv = writeConfigFile(self.siteConfig, self.siteConfigFileName)
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
        if section is None or section == "":  #main section
            self.siteConfig = merge(self.siteConfig, data)
        else:
            self.siteConfig = merge(self.siteConfig, {section : data})
        
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

def printDict(inDict, level):

    #print ("got indict ", inDict, inDict.keys, level)
    
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
            

#
def main():

    with configClass() as configuration:
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
    