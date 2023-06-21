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
    """Turn any string into an ASCII equivalent which can be used as a
    filename. (We don't want to worry about whether the filesystem supports
    UTF-8.)

    Different strings must always map to different strings; after that,
    human readability is nice. We don't have to reverse this mapping.
    """
    if not val:
        return '=='
    if pat_basictag.match(val):
        return val.replace(' ', '_')
    return pat_fancychar.sub(escapefancy, val)


pat_simpledate = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
pat_fulldate = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?(Z|[+]00:00)?$')

def parsedate(val):
    """Accept a date or datetime in ISO format:
      2023-05-01
      2023-05-01T12:00:00
    The "Z" or "+00:00" suffix is optional; we assume UTC whether it's there
    or not.
    Fractional seconds are accepted but trimmed out because seriously, why.
    If the date is not recognized, raise ValueError.
    """
    if not val:
        raise ValueError()
    if pat_simpledate.match(val):
        return val+'T12:00:00+00:00'
    match = pat_fulldate.match(val)
    if match:
        if match.group(1):
            return val[ : match.start(1) ] + '+00:00'
        elif match.group(2):
            return val[ : match.start(2) ] + '+00:00'
        else:
            return val + '+00:00'
    raise ValueError()


def relativetime(after, before):
    """Say (in English) how far apart two datetimes are.
    If they're more than a week apart, just report the later time.
    If they're in the wrong order, or separated by less than 15 minutes,
    return None.
    """
    if after <= before:
        return None
    
    diff = after - before
    if diff < datetime.timedelta(minutes=15):
        return None
    
    diffdays = diff / datetime.timedelta(days=1)
    if diffdays >= 8:
        if before.year != after.year:
            return after.strftime('%B %d, %Y').replace(' 0', ' ')
        else:
            return after.strftime('%B %d').replace(' 0', ' ')
    
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
