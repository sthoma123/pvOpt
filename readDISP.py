#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#
# für das Raspberry standard display (Helligkeit usw.)
# Achtung: wenn power ausgeschaltet wird, kann der screensaver nicht aufwecken.
# Achtung: ich kann den Status des Screensaver nicht abfragen, d.h. ich weiß nicht ob der Schirm eingeschaltet ist
# Achtung: ich vermute, dass das ausschalten des screensaver nicht möglich ist?
#
#
#
"""
A Python module for controlling power and brightness
of the official Raspberry Pi 7" touch display.

Ships with a CLI, GUI and Python API.

:Author: Linus Groh
:License: MIT license
"""
#from __future__ import print_function
print ("imported " + __name__)

import argparse
import os, glob, time, sys, datetime
import globals
import config
import logging
import cache
import driverCommon
from funcLog import logged
import metadata



__author__ = "Linus Groh"
__version__ = "1.7.1"
PATH = "/sys/class/backlight/rpi_backlight/"

#damit weckt man den Screensaver auf:
PATHBLANK = "/sys/class/graphics/fb0/"

def _perm_denied():
    logging.error("readDISP: access to %s denied" %(PATH))

def _get_value(name):
    try:
        with open(os.path.join(PATH, name), "r") as f:
            return f.read()
    except PermissionError:
        _perm_denied()

def _set_value(name, value, path = PATH):
    with open(os.path.join(path, name), "w") as f:
        f.write(str(value))

def get_actual_brightness():
    """Return the actual display brightness.

    :return: Actual brightness value.
    :rtype: int
    """
    return int(_get_value("actual_brightness"))


def get_max_brightness():
    """Return the maximum display brightness.

    :return: Maximum possible brightness value.
    :rtype: int
    """
    return int(_get_value("max_brightness"))


def get_power():
    """Return wether the display is powered on or not.

    :return: Whether the diplay is powered on or not.
    :rtype: bool
    """
    return not int(_get_value("bl_power"))


def set_brightness(value, smooth=False, duration=1):
    """Set the display brightness.

    :param value: Brightness value between 11 and 255
    :param smooth: Boolean if the brightness should be faded or not
    :param duration: Fading duration in seconds
    """
    max_value = get_max_brightness()
    if not isinstance(value, int):
        raise ValueError(
            "integer required, got '{}'".format(type(value)))
    if not 10 < value <= max_value:
        raise ValueError(
            "value must be between 11 and {}, got {}".format(max_value, value))

    if smooth:
        if not isinstance(duration, (int, float)):
            raise ValueError(
                "integer or float required, got '{}'".format(type(duration)))
        actual = get_actual_brightness()
        diff = abs(value-actual)
        while actual != value:
            actual = actual - 1 if actual > value else actual + 1

            _set_value("brightness", actual)
            time.sleep(duration/diff)
    else:
        _set_value("brightness", value)

def set_power(on):
    """Set the display power on or off.

    :param on: Boolean whether the display should be powered on or not
    """
    try:
        #print ("setting power to inverted %s -> %s " %(str(on), str(int(not on))))
        _set_value("bl_power", int(not on))
    except PermissionError:
        _perm_denied()

def setBlank(on):
    try:
        print ("setting blank to inverted %s -> %s " %(str(on), str(int(not on))))
        _set_value("blank", int(not on), PATHBLANK)
        
    except PermissionError:
        _perm_denied()
        
#----------------------------------------------------------------------------------------------------
# write operator:
def handleOperator(a, b, operator):
    rv = 0
    if type(a) in [int, float, bool]:
        if operator == "ADD":
            rv = a + b
        elif operator == "SUB":
            rv = a - b
        elif operator == "MUL":
            rv = a - b
        elif operator == "DIV":
            rv = a - b
        else:  #here comes the bitwise operators:
            a = int(a)
            b = int(b)
            if operator == "XOR":
                rv = a ^ b        
            elif operator == "OR":
                rv = a | b        
            elif operator == "AND":
                rv = a & b
    else:
        logging.error ("readDISP handleOperator got wrong datatype %s returning 0" % (str(type(a))))
    
    
    #print ("+++ handleOperator %s = %s %s %s" % (str(rv), str(a), operator, str(b)))
    
    return rv
    
#----------------------------------------------------------------------------------------------------
# write:
#   stores a variable in globals.var dictionary
#
@logged(logging.DEBUG)
def write(dp, value, dummy=None):  #3rd parameter needed for some other writes...
    #import web_pdb; web_pdb.set_trace() #debugging

    #print ("varWrite got %s, value %s " % (str(dp), str(value)))
    
    cmdList=["ADD", "SUB", "XOR", "OR", "AND", "MUL", "DIV"]
    operator = "SET"
    if type(dp) is str:
        dpList=dp.split('/')
    else:
        dpList=dp
        
    if dpList[0] in cmdList:
        operator=dpList[0]
        dpList=dpList[1:]
    
    dp="/".join(dpList)

    #    print ("varWrite step 2 %s, value %s " % (str(dp), str(value)))
    
    rv = metadata.read("DISP/" + dp, "DISP/" + dp)
    
    if operator in cmdList:
        rv = read(dp)
        value = handleOperator(rv[1], value, operator)

    stat = "Ok"
    r=0    

    if dp == "BLANK":
        setBlank(value)
        
    elif dp == "POWER":
        set_power(value)
        r = get_power()
        
    elif dp == "BRIGHT":
        set_brightness(value)
        r = get_actual_brightness()
        
    else:
        logging.error("readDISP.read got wrong datapoint: %s " % (dp))
        stat = "Error"
        r = 0

    rv[1] = r
    rv[5] = stat

    return rv


    
#----------------------------------------------------------------------------------------------------
# read:
#   reads a variable from globals.var dictionary
#   DISP/POWER
#   DISP/BRIGHT
#

@logged(logging.DEBUG)
def read(dp):
    
    rv = metadata.read("DISP/" + dp, "DISP/" + dp)

    try:
        
        if dp is None:
            logging.error("readDISP.read got no datapoint.")
        elif "" == dp:
            logging.error("readDISP.read got empty datapoint.")
            
        stat = "Ok"
        if dp == "BLANK" :
            r = get_power()
        elif dp == "POWER" :
            r = get_power()
        elif dp == "BRIGHT" :        
            r = get_actual_brightness()
        else:
            logging.error("readDISP.read got wrong datapoint.")
            stat = "Error wrong dp"
                        
        rv[1] = r
        rv[5] = stat
        
    except Exception as e:
        rv = "Exception %s, %s" % (type(e).__name__, e.args), 0, "~" , datetime.datetime.now(), dp, "Exception"
        logging.exception("readVar.py")
            
        
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
        print ("write power true %s" % str(write ("POWER", True)))
        print ("write bright 11 %s" % str(write ("BRIGHT", 11)))
        time.sleep (2)
        print ("write bright 100 %s" % str(write ("BRIGHT", 100)))
        time.sleep (2)
        print ("write bright 200 %s" % str(write ("BRIGHT", 200)))
        

# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
  main()
    
