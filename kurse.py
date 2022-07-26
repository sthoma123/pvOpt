#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß
print ("imported " + __name__)

import requests
import json

def quote(symbol):
    r = requests.get(
      'https://query1.finance.yahoo.com'+
      '/v7/finance/quote?symbols=%s'
      % symbol)
    data = json.loads(r.text)
    return (data['quoteResponse']
            ['result'][0]
            ['regularMarketPrice'])



print (quote("amz.de"))
