import re

pat_basictag = re.compile('^[a-z0-9 -]*$')
pat_fancychar = re.compile('[^a-z0-9-]')

def escapefancy(match):
    ch = match.group(0)
    if ch == ' ':
        return '_'
    return '=%X=' % (ord(ch),)

def tagfilename(val):
    if pat_basictag.match(val):
        return val.replace(' ', '_')
    return pat_fancychar.sub(escapefancy, val)

pat_simpledate = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
pat_fulldate = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?Z$')

def parsedate(val):
    if pat_simpledate.match(val):
        return val+'T12:00:00Z'
    match = pat_fulldate.match(val)
    if match:
        if match.group(1):
            return val[ : match.start(1) ]+'Z'
        else:
            return val
    return None

