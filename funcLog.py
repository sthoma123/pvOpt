#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß

# from imp import reload
# logging decorator
#       
print ("imported " + __name__)

import logging
import time
#import config
#import globals

from functools import wraps

# from: https://www.zopyx.com/andreas-jung/contents/a-python-decorator-for-measuring-the-execution-time-of-methods
#
global g_level 
g_level = 0
global g_path 
g_path = []
def timeit(method):

    def timed(*args, **kw):

        ts = time.process_time()
        global g_level
        global g_path
        
        g_level = g_level + 1
        g_path.append(method.__name__)
        result = method(*args, **kw)
        te = time.process_time()
        g_level = g_level - 1

        print ('%s %r | %2.2f | sec' % (".."*g_level, "/".join(g_path), te-ts))
        g_path.pop()
        
        return result

    return timed

    
def logged(level, name=None, message=None):
    '''
    Add logging to a function.  level is the logging
    level, name is the logger name, and message is the
    log message.  If name and message aren't specified,
    they default to the function's module and name.
    '''
    def decorate(func):
        logname = name if name else func.__module__
        log = logging.getLogger(logname)
        
        logmsg = message if message else func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            log.log(level, logmsg  + " called with " + str(args))
            #logging.error( logmsg  + " called with " + str(args))
            #print(level, logmsg  + " called with " + str(args))
            rv = func(*args, **kwargs)
            #logging.error( logmsg + " returns " + str(rv))

            log.log(level, logmsg + " returns " + str(rv))
            #print(level, logmsg  + " called with " + str(args))
            return rv
        return wrapper
    return decorate
