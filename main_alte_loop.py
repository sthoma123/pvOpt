#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
#  import web_pdb; web_pdb.set_trace() #debugging
# hauptprogramm: zeige alles und schalte:
# nun mit bewässerung
print ("imported " + __name__)

#Action="set"/ "get"
#bei set:
#- Value ="0,1,..n"

#bei get: (fuer verdichten)
#- lastvalue = "0,1,..n" 
# - timeout (?)

#bei get fuer Archiveserver:
#- timeframe = {start / end} (unixtime?)

#Zu den Values: unit

#DP=prot/box/ID/SUBID/SUBSUBID

#prot=PV, ETH, TEMP

#box = {PV: "PV0" | "PV1"}
#      {ETH:"KELLERSCHALTER1"}
#      {TEMP: "" | "KELLERRASPI"}  // important for archive server
#      {CURRENT: "" | "KELLERRASPI" }   // important for archive server
      
#ID =  {PV: "PAC"}
#      {ETH: "" | "1-8"}
#      {TEMP: "23a27dd" | ...} //1-Wire ID number
#      {CURRENT: "1.. "n"} //analog number

      
import os, time, sys, datetime
#import readETH008 as eth008
import readPV as PV
import readtemp as temp
import config
import logging
import globals
import driverCommon
import json
from funcLog import logged
import datetime

wohnzimmerschalter = "wohnzimmer"
zaehlerschalter = "zaehlerschalter"
kellerschalter = "kellerschalter"
keller2 = "keller2"
kuechenschalter = "kueche"

zaehlerSauna = -12  #invertiert

solarPumpeVerbrauch= 0.5  #in kW, sommerbetrieb da hängt derzeit das zweite batterieladegerät!
filterPumpeVerbrauch= 0.5
steckdoseVerbrauch = 0.05
saunaVerbrauch = 0.7

gHoldcycleSolarPumpe=0
gHoldcycleFilterPumpe=0
gCountHold=60  #600 sekunden, 10 minuten

REGELRESERVE=400
MAXUEBERSCHUSS=6500
MINBATCHARGE=50
MINPVPOWER=900

SOMMER=True # habe ladegerät angesteckt.


#----------------------------------------------------------------------------------------------------
@logged(logging.DEBUG)
def readstatus(dps, target): #network name of device
    #dats=driverCommon.readMultiViaWeb(json.dumps(dps), target=target)
    dats=driverCommon.readMultiViaWeb(dps, target=target)
    return dats


#--------------------------------------------------------------------------------
# negativer switch ist invertiert.
#
def setWithHyst(PAC, limitOn, hyst, switch, devicename):

    needed=0
    rv=""
    #rv = " " + str(switch)+":"
    x = None
    if PAC > limitOn:
        x=1
    if PAC < (limitOn-hyst):
        x=0
    if x is None:
        rv+="-"
    else:
        needed= x * limitOn
    
        if switch < 0: #invertiere ausgang
            switch=switch * -1
            if x==1: 
                x=0
            else:
                x=1
            
        #rv+=str(x)
        rv+= "*" if (x==1) else "."
        myWrite("ETH/"+devicename+"/"+str(switch), x, "kellerraspi:8000")
       
    return rv, needed

   
#--------------------------------------------------------------------------------
# getVarVerbrauch
#    
def getVarVerbrauch():

    dps1 = ("ETH/kellerschalter/3","ETH/kellerschalter/4","ETH/kellerschalter/5", "ETH/kellerschalter/1", "ETH/kellerschalter/2", "ETH/zaehlerschalter/12")
    #1: solarpumpe 1100W
    #2: beckenpumpe 500W
    #z9: Sauna 700W
    
    dats1 = readstatus(dps1, "kr:8000")
    wwStufe = int(dats1[0][1]) + int(dats1[1][1]) + int(dats1[2][1])
    wwKw = wwStufe * 1.500
    
    wwKw = wwKw + solarPumpeVerbrauch * int(dats1[3][1]) 
    wwKw = wwKw + filterPumpeVerbrauch * int(dats1[4][1])
    if int(dats1[5][1]) == 0: #invertiert
        wwKw = wwKw + saunaVerbrauch

    dps2 = ("ETH/kueche/13","ETH/kueche/14","ETH/kueche/15", "ETH/kueche/16", "ETH/kueche/17", "ETH/kueche/18", "ETH/kueche/19", "ETH/kueche/20")    
    dats2 = readstatus(dps2, "kr:8000")
    
    fbh=0
    for i in range(0,8):
        fbh += dats2[i][1]
        print ("kueche %d is %s" % (i, str(dats2[i][1])))
       
    print ("%d fussbodenstufen" % fbh)       
    wwKw = wwKw + 0.2 * fbh   
            

    print ("Warmwasser + Pumpen + Sauna brauchen: %6.2f" % wwKw)
    
    return wwKw
    
#--------------------------------------------------------------------------------
# getReserveViaZaehler
# neu!
# ich rechne hier in Watt!
#
def getReserveViaZaehler():

    dps1 = ("MOD/ttyUSB.modbus/1/ZAEHLER/SystemPower","MOD/ttyUSB.modbus/2/ZAEHLER/SystemPower")
    dats1 = readstatus(dps1, "zr:8000")

    #print ("getReserveViaZaehler got %s" % (str(dats1)))
    bilanz = 0
    if dats1[0][5] == "Ok" and dats1[1][5] == "Ok":
        bilanz = dats1[0][1] + dats1[1][1]   #negative Bilanz ist Einspeisung!!!
    
    print ("getReserveViaZaehler bilanz is %6.3f " %(bilanz))    
    wwKw = getVarVerbrauch() * 1000         
    reserve= (wwKw - bilanz) #    
    print ("Reserve ist: %6.2f" % reserve)
    
    return reserve



#--------------------------------------------------------------------------------
# getReserve
# wieviel reserve habe ich für warmwasser (d.h. Warmwasserstufe vom Verbrauch rausrechnen)
#
#

def getReserve():

    wwKw = getVarVerbrauch()

    PVDp = ["ALIAS/PVTotal"]
    PVData = readstatus(PVDp, "kr:8000")
    print ("got from PV: ", PVData)

    zaehlerDps = ("DLMS/ttyUSB.irKopf/1.7.0", "DLMS/ttyUSB.irKopf/2.7.0")
    zaehlerDats = readstatus(zaehlerDps, "zr:8000")
    #zaehlerDats= (1, ) # ignore
    #print ("got from zaehler: ", zaehlerDats)


    #bilanz=1 # keine zaehlerdaten; Annahme 1kW eigenverbrauch
    bilanz = - (PVData[0][1] / 1000) + wwKw + 0.200 # default: annahme 200w eigenverbrauch
    
    if len (zaehlerDats) > 1:
        try:
            if "ERROR" != zaehlerDats[0]:
                if zaehlerDats[0][5] == "Ok":
                    bilanz = float(zaehlerDats[0][1]) - float(zaehlerDats[1][1])
                    driverCommon.writeViaWeb("VAR/ZAEHLERBILANZ", bilanz, "kellerRaspi:8000")                    
                else:
                    logging.error('ZR antwortet, aber Zaehler nicht %s' % (zaehlerDats[0]))
            else:
                logging.error('ZR antwortet nicht %s, %s ' % (zaehlerDats[0], zaehlerDats[1]))
        except Exception as e:
            print ("getReserve: exception: %s" %(str(e)))
    
    
    verbrauch= bilanz + PVData[0][1] / 1000 - wwKw
    driverCommon.writeViaWeb("VAR/VERBRAUCH", verbrauch, "kellerRaspi:8000")                    

    #bilanz=1 # keine zaehlerdaten; Annahme 1kW eigenverbrauch
    bilanz = - (PVData[0][1] / 1000) + wwKw + 0.500 # default: annahme 200w eigenverbrauch
    reserve= (wwKw - bilanz) * 1000

    #setMainMessage ("Reserve ist: %6.2f" % reserve)
    
    return reserve
    
def myWrite(dp, value, target):
    driverCommon.writeViaWeb(dp, value, target)

    
def myRead(dp, host):
    rv=0
    rvTuple = driverCommon.readViaWeb(dp, None, host)
    if len(rvTuple)>1:
        rv=rvTuple[1]
    else:
        logging.error("main.py tries to read %s, got %s" % (dp, str(rvTuple)))
        rv=0
        
    return rv

#    
# returns true if bat within range
# retourniert cycle wann wieder getestet werden soll
#    
def checkBattspannung(cycle):
    spannung = myRead("ETH/Kueche/V", "kellerraspi:8000")
    rv = cycle
    print ("Spannung ist ", spannung)
    if spannung > 13.9:
        rv = cycle+20
        myWrite("ETH/"+kellerschalter+"/"+str(8), 1, "kellerraspi:8000") # ist  invertiert! -> entladen
        setMainMessage ("Überspannung %8.2f: hold off until %d!" %(spannung, rv))
        
    if spannung < 11.5: # ich hab 1v spannungsabfall bis zum ersten schalter!!!
        rv = cycle+20
        myWrite("ETH/"+kellerschalter+"/"+str(8), 0, "kellerraspi:8000") # ist  invertiert! -> laden
        setMainMessage ("Unterspannung %8.2f: hold on until %d!" %(spannung, rv))

    
    return rv




#--------------------------------------------------------------------------------
def allesAus():

    global gHoldcycleSolarPumpe
    global gHoldcycleFilterPumpe
    
    print ("Alle Verbraucher aus")
    #eth008.set_relais (zaehlerschalter, 12, 1)

    myWrite("ETH/"+kellerschalter+"/"+str(1), 0, "kellerraspi:8000")
    myWrite("ETH/"+kellerschalter+"/"+str(2), 0, "kellerraspi:8000")
    myWrite("ETH/"+kellerschalter+"/"+str(3), 0, "kellerraspi:8000")
    myWrite("ETH/"+kellerschalter+"/"+str(4), 0, "kellerraspi:8000")
    myWrite("ETH/"+kellerschalter+"/"+str(5), 0, "kellerraspi:8000")
    myWrite("ETH/"+kellerschalter+"/"+str(8), 1, "kellerraspi:8000")

    # wasser aus
    myWrite("ETH/"+keller2+"/"+str(13), 0, "kellerraspi:8000")
    myWrite("ETH/"+keller2+"/"+str(14), 1, "kellerraspi:8000")
    myWrite("ETH/"+keller2+"/"+str(15), 0, "kellerraspi:8000")
    myWrite("ETH/"+keller2+"/"+str(16), 1, "kellerraspi:8000")

    gHoldcycleSolarPumpe=0
    gHoldcycleFilterPumpe=0
    
    for i in range(13,21):  #bodenheizung
       myWrite("ETH/"+kuechenschalter+"/"+str(i), 0, "kellerraspi:8000")
       print ("off: kueche %d " % i)
    

#--------------------------------------------------------------------------------
def setMainMessage(s):    
    st = driverCommon.writeViaWeb("VAR/mainMessage/text", s, "kellerraspi:8000")

def setEVStatus(s):
    s = "%s %s" % (s,time.strftime("%Y_%m_%d %H_%M_%S"))
    st = driverCommon.writeViaWeb("VAR/evStatus/text", s, "kellerraspi:8000")

#--------------------------------------------------------------------------------
# retourniert prozent Batterie und power zur Batterie
#
def getBXState():
   # battery percentage, power, pvPower
    dps1 = "BX/BATTERX/1074", "BX/BATTERX/1121", "BX/BATTERX/1634"
    dats1 = readstatus(dps1, "kr:8000")
    
    cap=0
    power=0
    pvPower = 0

    if len(dats1) > 2:
        if len(dats1[0])> 5 and len(dats1[1])>5 and len(dats1[2])>5 :
            if dats1[0][5] == "Ok" and dats1[1][5] == "Ok" and dats1[2][5] == "Ok":
                cap = dats1[0][1]
                power = dats1[1][1]
                pvPower = dats1[2][1]
                
    return cap, power,  pvPower




#--------------------------------------------------------------------------------
# retourniert bilanz zwischen den beiden Zaehlern:
#
def getUeberschuss():
 
    #dps1 = ("MOD/ttyUSB.modbus/1/ZAEHLER/SystemPower","MOD/ttyUSB.modbus/2/ZAEHLER/SystemPower")
    dps1 = ("DLMS/ttyUSB.irKopf/1.7.0", "DLMS/ttyUSB.irKopf/2.7.0")
    dats1 = readstatus(dps1, "zr:8000")

    print ("getReserveViaZaehler got %s" % (str(dats1)))
    
    ueberschuss = 0
    print ("readStatus Zaehler returns %s" % (dats1))
    
    if len(dats1) > 1:
        if len(dats1[0])> 5 and len(dats1[1])>5:
            if dats1[0][5] == "Ok" and dats1[1][5] == "Ok":
                ueberschuss = dats1[1][1] - dats1[0][1]    #einspeisung - bezug
    
    print ("getUeberschuss is %6.3f " %(ueberschuss))    
    #setMainMessage("getUeberschuss is %6.3f " %(ueberschuss))    

    return ueberschuss

#--------------------------------------------------------------------------------
#
#  retourniert das was ich zu verbrauchen glaube.
#
def setzeVerbraucher (zuVerbrauchen, cycle, battLaderFrei, aussentemp, autoBoden, autoBoiler, corrFactorBatt):

    global gHoldcycleSolarPumpe
    global gHoldcycleFilterPumpe
    PACOffset = 50                           # zuVerbrauchen fuer zählerungenauigkeit bzw. totzeit.
    
    
    #s="setzeVerbraucher: zuVerbrauchen ist %6.0f W" % (zuVerbrauchen)
    s=""
    sk=""

    verbraucht = 0
    if zuVerbrauchen > MAXUEBERSCHUSS:  # begrenzen auf ca. 3kW
        zuVerbrauchen = MAXUEBERSCHUSS
        s=s+"+ "
        
    
    if battLaderFrei:
        ss, vv = setWithHyst(zuVerbrauchen, PACOffset+1000*steckdoseVerbrauch, 10, -8, kellerschalter) #steckdose, battlader
        s+=ss
        verbraucht+=vv

    if SOMMER:        
        if cycle > gHoldcycleFilterPumpe:
            ss, vv = setWithHyst(corrFactorBatt + zuVerbrauchen - verbraucht, PACOffset+1000*filterPumpeVerbrauch, 100, 2, kellerschalter) #filter
            s+=ss
            verbraucht+=vv
            if vv > 0:
                gHoldcycleFilterPumpe = cycle + gCountHold
                logging.error('Main: filter: Setzeverbraucher %d = %d + %d' % (gHoldcycleFilterPumpe, cycle, gCountHold))
        else:
            # ist zwar eingeschaltet, sollte aber nicht...
            verbraucht+=filterPumpeVerbrauch
            s+=" Filter :H(%d)" % gHoldcycleFilterPumpe

        #solar erst einschalten, wenn filter läuft, und aussentemp > 20 Grad ist.
        
        if  cycle > gHoldcycleSolarPumpe:
#            if aussentemp > 20:
            ss=""
            vv=0
#solar wird vom differenzregler gesteuert, daher nix setzen hier:            ss, vv = setWithHyst(zuVerbrauchen-verbraucht, PACOffset+1000*solarPumpeVerbrauch, 100, 1, kellerschalter) #solar
#            else:
#            ss = " 1:0 (%5.2f) " % aussentemp
#            vv = 0
#            eth008.set_relais (kellerschalter, 1, 0)
                
            s+=ss
            verbraucht+=vv
            if vv > 0:
                gHoldcycleSolarPumpe = cycle + gCountHold
                logging.error('Main: solar: Setzeverbraucher %d = %d + %d' % (gHoldcycleSolarPumpe, cycle, gCountHold))

        else:
            # ist offenbar noch eingeschaltet:
            # ist zwar eingeschaltet, sollte aber nicht...
            verbraucht+=1000*solarPumpeVerbrauch
            s+=" 1:H(%d)" % gHoldcycleSolarPumpe
    #endif sommer    

##boilertemp sollte ich auch noch berücksichtigen!            

    if autoBoiler:
        ss, vv = setWithHyst(zuVerbrauchen - verbraucht, PACOffset+1500, 100, int(3+((cycle/100)%3)), kellerschalter)
        s+=ss
        verbraucht+=vv
    
    #ss, vv = setWithHyst(zuVerbrauchen - verbraucht, PACOffset+1000*saunaVerbrauch, 100, zaehlerSauna, zaehlerschalter) #sauna
    #s+=ss
    #verbraucht+=vv


#fussboden:
    if autoBoden:
        ss, vv = setWithHyst(zuVerbrauchen - verbraucht, PACOffset+300, 100, int(13+((cycle/100)%8)), kuechenschalter)
        sk+=ss
        verbraucht+=vv

        ssk, vv =setWithHyst(zuVerbrauchen - verbraucht, PACOffset+300, 100, int(13+((cycle/100+1)%8)), kuechenschalter)
        sk+=ssk
        verbraucht+=vv

    #Bodenheizung hat priorität gegen zweite Warmwasser

    if autoBoiler:
        ss, vv = setWithHyst(zuVerbrauchen - verbraucht, PACOffset+1500, 100, int(3+((cycle/100+1)%3)), kellerschalter)
        s+=ss
        verbraucht+=vv


    if autoBoden:
        ssk, vv =setWithHyst(zuVerbrauchen - verbraucht, PACOffset+300, 100, int(13+((cycle/100+2)%8)), kuechenschalter)
        sk+=ssk
        verbraucht+=vv

        ssk, vv =setWithHyst(zuVerbrauchen - verbraucht, PACOffset+300, 100, int(13+((cycle/100+3)%8)), kuechenschalter)
        sk+=ssk
        verbraucht+=vv
        

        ssk, vv =setWithHyst(zuVerbrauchen - verbraucht, PACOffset+300, 100, int(13+((cycle/100+4)%8)), kuechenschalter)
        sk+=ssk
        verbraucht+=vv

        ssk, vv =setWithHyst(zuVerbrauchen - verbraucht, PACOffset+300, 100, int(13+((cycle/100+5)%8)), kuechenschalter)
        sk+=ssk
        verbraucht+=vv

        ssk, vv =setWithHyst(zuVerbrauchen - verbraucht, PACOffset+300, 100, int(13+((cycle/100+6)%8)), kuechenschalter)
        sk+=ssk
        verbraucht+=vv
        

        ssk, vv =setWithHyst(zuVerbrauchen - verbraucht, PACOffset+300, 100, int(13+((cycle/100+7)%8)), kuechenschalter)
        sk+=ssk
        verbraucht+=vv
        
    
    if autoBoiler:
        ## boiler nur 2 stufen: letzte immer ausschalten
        ss, vv = setWithHyst(0, PACOffset+1500, 100, int(3+((cycle/100+2)%3)), kellerschalter)
        s+=ss
        verbraucht+=vv

    print ("setzeVerbraucher: verbraucht %5.2f" % verbraucht)
    print ("kellerschalter: ", s)
    print ("kuechenschalter: ", sk)
    
    setEVStatus("%5.2fW,<br> K:%s,<br> Boden:%s" % (verbraucht, s, sk))
    return verbraucht
    
#-------------------------------------------------------------------------------------
#
#
#  getAussentemp retourniert aussentemperatur (ein float)
#    
def getAussentemp():
    rv = myRead("TEMP/00042d9aabff", "kellerraspi:8000")
    return rv

#-------------------------------------------------------------------------------------
#  just a try when a button is pressed.
#
def toggleForButton1():
    #dp = "ETH/WOHNZIMMER/15"
    dp = "ETH/KELLER2/7"
    target = "kellerraspi:8000"
    stat = myRead(dp, target)
    stat = not stat
    myWrite(dp, stat, target)
    print ("toggleForButton1: set %s to %s " %(dp, str(stat)))
    

#-------------------------------------------------------------------------------------
#
#
def execTimerWasser(auto, oldAuto, offSwitch, onSwitch, timeWaterOn, timeWaterOff):
    txt = {13: "Wasser", 15: "Buesche"}
                
    if auto:
        now = datetime.datetime.now()
        oldWasserState=myRead("ETH/"+keller2+"/"+str(onSwitch), "kellerraspi:8000")
        #print("read keller2 %s oldWasserState is %s " % (str(onSwitch), str(oldWasserState)))
        
        if (now > timeWaterOn) and (now < timeWaterOff):
            # wasser ein
            myWrite("ETH/"+keller2+"/"+str(onSwitch), 1, "kellerraspi:8000")
            myWrite("ETH/"+keller2+"/"+str(offSwitch), 0, "kellerraspi:8000")
            if oldWasserState != True:
                setMainMessage("%s - auto - ein" % txt[onSwitch])
        else:
            # wasser aus
            myWrite("ETH/"+keller2+"/"+str(onSwitch), 0, "kellerraspi:8000")
            myWrite("ETH/"+keller2+"/"+str(offSwitch), 1, "kellerraspi:8000")
            if oldWasserState != False:
                setMainMessage("%s - auto - aus" % txt[onSwitch])

    else: #sicherheitshalber einmal ausschalten
        if oldAuto != auto:
            # wasser aus
            myWrite("ETH/"+keller2+"/"+str(onSwitch), 0, "kellerraspi:8000")
            myWrite("ETH/"+keller2+"/"+str(offSwitch), 1, "kellerraspi:8000")
            
            
#-------------------------------------------------------------------------------------
#
#
#  Main
#    
def main():

    global gHoldcycleSolarPumpe
    global gHoldcycleFilterPumpe

    stopreason = "unknown"

    try:
        time.sleep(10)   # wait until server port is up&running
        cycle=0          #lifecycle
        gHoldcycleSolarPumpe=0
        gHoldcycleFilterPumpe=0
        oldWasserState= False
        oldAutoWasser = False
        oldAutoBuesche = False
        allesAus()
        
    

        holdcycle=0      #timeout für checkbatteriespannung
        
        ueberschuss=0    # Regelvariable, die mittels warmwasser und fbh auf null geregelt werden soll
        warmwasserEtc=0  # aktuell eingeschaltete Verbraucher
        
        setMainMessage("Main started")
        oldbutton1 = myRead("VAR/BUTTON1", "kellerraspi:8000")
        #import web_pdb; web_pdb.set_trace() #debugging
        
        while 1:
        
            button1 = myRead("VAR/BUTTON1", "kellerraspi:8000")
            if (oldbutton1 != button1) :
                setMainMessage("togglebutton1")
                toggleForButton1()
                
            oldbutton1 = button1
            
            
            # Boiler, Draussen, Wohnzimmer
            autoBoiler = myRead("VAR/AUTOBOILER", "kellerraspi:8000")
            autoBoden = myRead("VAR/AUTOBODEN", "kellerraspi:8000")


            #temps= [temp.read(s) for s in ("/00042b8679ff", "/00042d9aabff", "/00042cb4d4ff")]             
            #PAC=PV.getTotalPAC()            
            #PAClist = PV.read("/") # total PAC
            
            #PAClist = driverCommon.read("PV/")

            #PAC=PAClist[1]
            #s= ( str(datetime.datetime.now())+" " +
            #   PAClist[0] + " " + str(PAClist[1]) + " " + PAClist[2] + " " +
            #    ", ".join([temp[0] + " " + str(temp[1]) + " " + temp[2]for temp in temps]) 
            #   )
               
            #reserve =  getReserve()
            #reserve = getReserveViaZaehler()
            
            if autoBoiler or autoBoden:
                cycle=cycle+1            
                st = driverCommon.writeViaWeb("VAR/LIFECYCLE", cycle, "kellerraspi:8000")
                ueberschuss = getUeberschuss() - REGELRESERVE # reserve
                
                if holdcycle < cycle:  # andernfalls wird battspannung geregelt!
                    holdcycle = checkBattspannung(cycle)
                    
                if holdcycle > cycle:
                    battLaderFrei = False
                else:
                    battLaderFrei = True
                
                aussentemp = getAussentemp()
                
                battPercent, battPower, pvPower = getBXState()
                #
                # je voller die Batterie ist, desto mehr kann ich abzweigen (linear)
                # achtung: wenn schaltvorgänge sind, kann die zählerbilanz manchmal auf ein Einspeisung deuten
                # erweiterung: MINBATCHARGE abhängig von Tageszeit
                
                if battPercent < MINBATCHARGE or pvPower < MINPVPOWER or battPower < 0:  # nix zu verschenken.
                    ueberschuss=0
                    corrFactorBatt = 0
                else:
                    corrFactorBatt = 0
                    fact = (battPercent-MINBATCHARGE)* (100/MINBATCHARGE) / 100 
                    corrFactorBatt = battPower * fact
                    
                print ("battery State is pvPower %s, percent %s, power %s, corrFactorBatt is %s " %(str(pvPower), str(battPercent), str(battPower), str(corrFactorBatt)))
                
                warmwasserEtc = setzeVerbraucher (ueberschuss+warmwasserEtc, cycle, battLaderFrei, aussentemp, autoBoden, autoBoiler, corrFactorBatt)
                
            else:
                allesAus()
                warmwasserEtc = 0
            
            while 1:
                time.sleep(10)
                autoBoiler = myRead("VAR/AUTOBOILER", "kellerraspi:8000")
                autoBoden = myRead("VAR/AUTOBODEN", "kellerraspi:8000")
                autoWasser = myRead("VAR/AUTOWASSER", "kellerraspi:8000")
                autoBuesche = myRead("VAR/AUTOBUESCHE", "kellerraspi:8000")
                
                if oldAutoWasser != autoWasser:
                    setMainMessage("Wasser - %s" % ("auto" if autoWasser else "manual"))
                    
                if oldAutoBuesche != autoBuesche:
                    setMainMessage("Buesche - %s" % ("auto" if autoWasser else "manual"))
                    
                now = datetime.datetime.now()
                timeWaterOn = datetime.datetime(now.year, now.month, now.day, 6,0,0)
                timeWaterOff = datetime.datetime(now.year, now.month, now.day, 7,0,0)
                execTimerWasser(autoWasser, oldAutoWasser, 14,13, timeWaterOn, timeWaterOff)
                execTimerWasser(autoBuesche, oldAutoBuesche, 16,15, timeWaterOn, timeWaterOff)

                timeWaterOn = datetime.datetime(now.year, now.month, now.day, 19,0,0)
                timeWaterOff = datetime.datetime(now.year, now.month, now.day, 20,0,0)
                execTimerWasser(autoWasser, oldAutoWasser, 14,13,timeWaterOn, timeWaterOff)
                execTimerWasser(autoBuesche, oldAutoBuesche, 16,15, timeWaterOn, timeWaterOff)
                        
                oldAutoWasser = autoWasser
                oldAutoBuesche = autoBuesche

                if  autoBuesche or autoWasser or autoBoiler or autoBoden:   # kann ich nun damit unterbrechen und manuell bedienen.
                    break
                allesAus()
                setMainMessage("auto - off")

                while not autoWasser and not autoBuesche and not autoBoden and not autoBoiler:
                    if not (holdcycle < cycle):
                        holdCycle = (2 * cycle) - checkBattspannung(cycle)  # wird trotzdem geregelt!
                    time.sleep(10)
                    autoBoiler = myRead("VAR/AUTOBOILER", "kellerraspi:8000")
                    autoBoden = myRead("VAR/AUTOBODEN", "kellerraspi:8000")
                    autoWasser = myRead("VAR/AUTOWASSER", "kellerraspi:8000")
                    autoBuesche = myRead("VAR/AUTOBUESCHE", "kellerraspi:8000")
                    cycle=cycle + 1
                    st = driverCommon.writeViaWeb("VAR/LIFECYCLE", cycle, "kellerraspi:8000")
                setMainMessage("auto - on")

    except KeyboardInterrupt:
        stopreason="KeyboardInterrupt"
        pass
         
    except Exception as e:
        stopreason="exception"
        logging.exception ("main.py: got exception")
        
    allesAus()
    #st = driverCommon.writeViaWeb("VAR/mainMessage/text", "main stopped", "kellerraspi:8000")
    setMainMessage("main stopped(%s)" % stopreason)
       
    logging.debug('main stopped(%s)' % stopreason)        
    setEVStatus("main stopped (%s)" % stopreason)


#--------------------------------------------------------------------------------
# main
# Your program goes here.
# You can access command-line arguments using the args variable.
if __name__ == '__main__':
    with config.configClass() as configuration:
        globals.config= configuration
        config.createPID("/run/PVmain.pid")

        try:

            while True:        
                main()
                setMainMessage("main loop restart")

        finally:
            os.unlink("/run/PVmain.pid")



