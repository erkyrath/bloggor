
from jinja2.ext import Extension

class TagFilename(Extension):
    def __init__(self, env):
        env.filters['tagfilename'] = tagfilename

class SplitAtMore(Extension):
    def __init__(self, env):
        env.filters['splitatmore'] = splitatmore
        
from bloggor.util import tagfilename, splitatmore
