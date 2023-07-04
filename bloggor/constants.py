from enum import Enum, IntFlag
import pytz

class FileType(Enum):
    HTML = 'html'
    MD = 'md'
    WHTML = 'whtml'
    TXT = 'txt'

class FeedType(Enum):
    RSS = 'rss'
    ATOM = 'atom'

class Depend(IntFlag):
    EXIST    = 1
    TITLE    = 2
    BODY     = 4
    TAGS     = 8
    PUBDATE  = 16
    UPDATE   = 32
    COMMENTS = 64
    
eastern_tz = pytz.timezone('US/Eastern')
