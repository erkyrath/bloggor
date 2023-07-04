from enum import Enum, IntFlag
import pytz

class FileType(Enum):
    HTML = 'html'
    MD = 'md'
    WHTML = 'whtml'
    TXT = 'txt'

def parse_filetype(val):
    val = val.lower()
    if val == 'text':
        return FileType.TXT
    return FileType(val)
    
class FeedType(Enum):
    RSS = 'rss'
    ATOM = 'atom'

class Depend(IntFlag):
    NONE     = 0
    CREATED  = 1
    TITLE    = 2
    BODY     = 4
    TAGS     = 8
    PUBDATE  = 16
    UPDATE   = 32
    COMMENTS = 64

    ALL = CREATED|TITLE|BODY|TAGS|PUBDATE|UPDATE|COMMENTS
    ALLBUTBODY = CREATED|TITLE|TAGS|PUBDATE|UPDATE|COMMENTS

def parse_depend(val):
    if ',' in val:
        res = Depend.NONE
        for subval in val.split(','):
            res |= parse_depend(subval)
        return res
    val = val.upper()
    if val == 'TAG':
        return Depend.TAGS
    if val == 'COMMENT':
        return Depend.COMMENTS
    if val == 'ALL':
        return Depend.ALL
    if val == 'NONE':
        return Depend.NONE
    for dep in Depend:
        if dep.name == val:
            return dep
    raise ValueError(val)
    
eastern_tz = pytz.timezone('US/Eastern')
