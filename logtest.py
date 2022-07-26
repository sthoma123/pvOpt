#!/usr/bin/python3
print ("imported " + __name__)

import os, glob, time, sys, datetime
import logging
from funcLog import logged
            
LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}
                  
                  

def main(): 
    print ("LogTest started");
    fn="/var/log/pvOpt.log"
    print ("tail -f %s" % (fn))
    logging.basicConfig(filename=fn,format='%(asctime)s--%(threadName)s-%(name)s--%(levelname)s--%(message)s')
    logging.getLogger().setLevel(20)

    logging.error("LogTest logs error")
    logging.warning("LogTest logs warning")
    logging.info("LogTest logs info")
    logging.debug("LogTest logs debug")
    
    print ("LogTest finished");



# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()

