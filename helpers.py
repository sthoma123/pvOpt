#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
# globals for logging und configuration 

import re

#---------------------------
# returns modified string and count
#
def regular(source, regDp, subst):
    #print ("regular source %s reg %s subst %s" % (str(source), str(regDp), str(subst)))
    assert type(source) is str and type(regDp) is str and type(subst) is str, "regular expects strings, got sourc=%s, regDp=%s subst=%s" % (str(type(source)), str(type(regDp)), str(type(subst)))

    p = re.compile(regDp)
    if subst != "":
        return p.subn(subst, source)
    else:
        cnt = 0
        m = p.match(source)
        if m:
            cnt = 1

        return source, cnt


#----------------------------------------------------------------------------------------------------
# myConvert
#
# Exceptions werden mit Absicht durchhgeworfen!
#
def myConvert(value, TYP):
    rv = 0
    
    if TYP is int:
        rv = int(value)
    elif TYP is bool:
        rv = bool(value)
    elif TYP is float:
        rv = float(value)
    else:
        raise Exception("myConverty does not know type %s " % (str(TYP)))
    
    return rv
    

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


#---------------------------------------------------------------
def printError(s):
    return print (bcolors.FAIL + str(s) + bcolors.ENDC)

