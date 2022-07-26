
            
            


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
            
                
                
            else:
                allesAus()
                warmwasserEtc = 0
            
            while 1:
                

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
                    
                setMainMessage("auto - on")
