import traceback
import serial
import modbus_tk.defines as tkCst
import modbus_tk.modbus_rtu as tkRtu

import minimalmodbus as mmRtu

from pymodbus.client.sync import ModbusSerialClient as pyRtu

slavesArr = [2]
iterSp = 100
regsSp = 10
portNbr = 21
portName = 'com22'
baudrate = 153600

timeoutSp=0.018 + regsSp*0
print "timeout: %s [s]" % timeoutSp


mmc=mmRtu.Instrument(portName, 2)  # port name, slave address
mmc.serial.baudrate=baudrate
mmc.serial.timeout=timeoutSp

tb = None
errCnt = 0
startTs = time.time()
for i in range(iterSp):
  for slaveId in slavesArr:
    mmc.address = slaveId
    try:
        mmc.read_registers(0,regsSp)
    except:
        tb = traceback.format_exc()
        errCnt += 1
stopTs = time.time()
timeDiff = stopTs  - startTs

mmc.serial.close()

print mmc.serial

print "mimalmodbus:\ttime to read %s x %s (x %s regs): %.3f [s] / %.3f [s/req]" % (len(slavesArr),iterSp, regsSp, timeDiff, timeDiff/iterSp)
if errCnt >0:
    print "   !mimalmodbus:\terrCnt: %s; last tb: %s" % (errCnt, tb)



pymc = pyRtu(method='rtu', port=portNbr, baudrate=baudrate, timeout=timeoutSp)

errCnt = 0
startTs = time.time()
for i in range(iterSp):
  for slaveId in slavesArr:
    try:
        pymc.read_holding_registers(0,regsSp,unit=slaveId)
    except:
        errCnt += 1
        tb = traceback.format_exc()
stopTs = time.time()
timeDiff = stopTs  - startTs
print "pymodbus:\ttime to read %s x %s (x %s regs): %.3f [s] / %.3f [s/req]" % (len(slavesArr),iterSp, regsSp, timeDiff, timeDiff/iterSp)
if errCnt >0:
    print "   !pymodbus:\terrCnt: %s; last tb: %s" % (errCnt, tb)
pymc.close()


tkmc = tkRtu.RtuMaster(serial.Serial(port=portNbr, baudrate=baudrate))
tkmc.set_timeout(timeoutSp)

errCnt = 0
startTs = time.time()
for i in range(iterSp):
  for slaveId in slavesArr:
    try:
        tkmc.execute(slaveId, tkCst.READ_HOLDING_REGISTERS, 0,regsSp)
    except:
        errCnt += 1
        tb = traceback.format_exc()
stopTs = time.time()
timeDiff = stopTs  - startTs
print "modbus-tk:\ttime to read %s x %s (x %s regs): %.3f [s] / %.3f [s/req]" % (len(slavesArr),iterSp, regsSp, timeDiff, timeDiff/iterSp)
if errCnt >0:
    print "   !modbus-tk:\terrCnt: %s; last tb: %s" % (errCnt, tb)
tkmc.close()
