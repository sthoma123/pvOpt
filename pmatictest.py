#!/usr/bin/python3

import pmatic
ccu = pmatic.CCU (address="192.168.0.189", credentials=("Admin", ""))

#for device in ccu.devices.query(device_type="HM-Sec-SC"):#
# device.is_open and "open" or "closed")

for device in ccu.devices.query(device_type="HM-LC-Sw1-FM"):
    print("%-20s %6s" % (device.name, str(device)))
