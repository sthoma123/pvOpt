import archive

x=archive.stringToBuf("asfdasfd")
y=archive.bufToString(x)
print (y)

ff=123.456

bb=archive.floatToBuf(ff)

print (bb)

cc=archive.bufToFloat(bb)

print (cc)



import datetime

no=datetime.datetime.now()

x=archive.timeToBuf(no)
print (x)

y=archive.bufToTime(x)
print (y)

