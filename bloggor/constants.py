from enum import Enum
import pytz

HTML = 'html'
MD = 'md'
WHTML = 'whtml'
TXT = 'txt'

class FeedType(Enum):
    RSS = 'rss'
    ATOM = 'atom'

eastern_tz = pytz.timezone('US/Eastern')
