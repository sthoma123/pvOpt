#!/usr/bin/python3

import os, glob, time, sys, datetime
import json, logging
import configparser
import optparse
import parser

# set theh following variable to True if you don't want me to grab the arguments
doNotParseCommandline = False
print("config.py sets doNotPars to False!")

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


def getConfig(configfilename):
    
    rv = dict()
    conf = configparser.ConfigParser()
    conf.optionxform = lambda option: option
    conf.read(configfilename)  
    rv.update(conf["main"])
    
    for ke in conf.sections():            
        if ke != "main":
            rv.update({ke:dict()})
            rv[ke].update(conf[ke])
    # check if there are json strings: decode them
    lists={}
    for var in rv.keys():
      if var[0:5] == "json_":
        lists.update({var[5:]: json.loads(rv[var])})
    rv.update(lists)
    
    return rv


class configClass:
    def __init__(self):        
        self.configfilename='/etc/pvOpt.ini'

        try:
            self.__dict__["include"] = self.configfilename
            while "include" in self.__dict__:
                includes=self.__dict__["include"]
                self.__dict__.pop("include", None)
                #del self.__dict__['include']
                for fn in includes.split(","):
                    confData=getConfig(fn)
                    self.__dict__.update(confData)
                
            print ("doNot... is %s"%str(doNotParseCommandline))
            if not doNotParseCommandline:
                print ("config: get commandline arguments")
                
                #commmandline overrides configfile (for debuglevels etc.)
                parser = optparse.OptionParser()
                parser.add_option('-l', '--logging-level', help='Logging level, e.g. debug, warning, info, error, critical')
                parser.add_option('-f', '--logging-file', help='Logging file name, e.g. /var/log/pvOpt.log')
                
                (options, args) = parser.parse_args()
                
                if type(options.logging_file) is str and options.logging_file != "" :
                    self.logfilename=options.logging_file
                    
                if not options.logging_level is None:
                    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
                    self.debugLevel = logging_level
                
            #if "debugLevel" in self.__dict__:
            #        print ("logging with level ", self.debugLevel)            
                
            #if "logfilename" in self.__dict__:
            #    print ("logging to logfilename ", self.logfilename)
                
        except Exception as e:
            print ("exception during creation of config object %s: %s" %(self.configfilename, str(e)))
            logging.exception("creation of config object")
            
        
        # ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        if hasattr(self, "logfilename"): 
            try:
                logging.basicConfig(filename=self.logfilename,level=int(self.debugLevel), format='%(asctime)s--%(threadName)s-%(name)s--%(levelname)s--%(message)s')
            except Exception as e:
                print ("unable to log to %s: %s" %(self.logfilename, str(e)))

    def __enter__(self):
    # read from file:
        try:    
            #json.dump(<self.__dict__, open('/opt/pvOpt/config.json', 'w'))
            configIni.read(configuration.logfilename)

        except:
            pass
        return self

    #  

    def __exit__(self, type, value, traceback):
        pass
        
#with configClass() as config:
    #config=configClass()
    
    #print (config.Tempsensors)
    #print("-----------------")
    #print (config.Devicenames)
    #print("-----------------")
    #print (config.__dict__)


    
#----------------------------------------------------------------------------------------------------
# MAIN:
#
#-------------------------------------------------------------------------
#

def printDict(inDict, level):

    #print ("got indict ", inDict, inDict.keys, level)
    
    for key in inDict.keys():
        sys.stdout.write("-" * (1+level)) # Ausgabe
        sys.stdout.write("%20s :" % key)        
        if type(inDict[key]) is dict:
            sys.stdout.write("\r\n")
            printDict(inDict[key], level + 1)
        else:
            if inDict[key] is str:
                s=inDict[key]
            else:
                s=str(inDict[key])
                
            sys.stdout.write(s)
            sys.stdout.write("\r\n")
            

#
def main():

    with configClass() as configuration:
        print ("config has:")
        printDict(configuration.__dict__, 0)
            
        
        
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()
    