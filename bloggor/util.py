import re
import datetime
from collections.abc import MutableMapping

class MultiDict(MutableMapping):
    def __init__(self):
        self.map = {}

    def __repr__(self):
        return '<MultDict %r>' % (self.map,)

    def keys(self):
        return self.map.keys()

    def __getitem__(self, key):
        return self.map[key]

    def __setitem__(self, key, val):
        self.map[key] = val

    def __delitem__(self, key):
        del self.map[key]

    def __len__(self):
        return len(self.map)

    def __iter__(self):
        return self.map.__iter__()

    def add(self, key, val):
        if key not in self.map:
            self.map[key] = [ val ]
        else:
            self.map[key].append(val)

    def totallen(self):
        return sum([ len(ls) for ls in self.map.values() ])

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


def relativetime(updatup, pubtup):
    if updatup <= pubtup:
        return None
    
    diff = updatup - pubtup
    diffdays = diff / datetime.timedelta(days=1)
    if diffdays >= 8:
        if pubtup.year != updatup.year:
            return updatup.strftime('%B %d, %Y').replace(' 0', ' ')
        else:
            return updatup.strftime('%B %d').replace(' 0', ' ')
    
    if diffdays > 0.999:
        val = round(diffdays)
        if val > 1:
            return '%d days later' % val
        else:
            return '1 day later'

    diffhours = diff / datetime.timedelta(hours=1)
    if diffhours > 0.999:
        val = round(diffhours)
        if val > 1:
            return '%d hours later' % val
        else:
            return '1 hour later'

    return 'straightaway'
    
def splitatmore(val):
    pos = val.find('<!--more-->')
    if pos < 0:
        return None
    else:
        return val[ : pos ]
