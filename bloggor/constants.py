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
    TITLE    = 1
    BODY     = 2
    TAGS     = 4
    PUBDATE  = 8
    UPDATE   = 16
    COMMENTS = 32
    
eastern_tz = pytz.timezone('US/Eastern')
