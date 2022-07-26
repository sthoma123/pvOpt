#!/usr/bin/python3
import json

def JSONDateTimeHandler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise (TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))
