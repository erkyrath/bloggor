
from jinja2.ext import Extension

class TagFilename(Extension):
    def __init__(self, env):
        env.filters['tagfilename'] = tagfilename

from bloggor.util import tagfilename
