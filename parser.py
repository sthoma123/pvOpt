# -*- coding: UTF-8 -*-
# probe for umlauts: öäüÖÄÜß

def myParser(s):
    def parseHelper(level=0):
        print ("Level %d" % level)
        
        rv = [""]
        while 1:
            try:
                token = next(tokens)
                print (token, str(rv))
                
            except StopIteration:
                if level != 0:
                    raise Exception('missing closing paren')
                else:
                    return rv
            if token == '*':  #split on same level (unit separator)
                rv.extend([""])
            elif token == '&':  #split on same level (some other indicator)
                rv.extend([""])                
            elif token == ')':
                if level == 0:
                    raise Exception('missing opening paren')
                else:
                    return [rv]
            elif token == '(':
                rv.extend(parseHelper(level+1))
            else:
                print ("Add" + token)
                rv[-1] = rv[-1] + token
                #return [token] + parseHelper(level)
    tokens = iter(s)
    return parseHelper()
    

#>>> d=[a,b]
#>>> d.extend([d])
#>>> d
#['asdf', 'rewq', [...]]
#>>> d.extend([c])
#>>> d
#['asdf', 'rewq', [...], 'oiuz']    



#print (myParser("2.6.0*00&bli(0.000*kWh)(00-00-00 00:00)")    )
    