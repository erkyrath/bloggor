import os.path

class Page:
    def __init__(self, ctx):
        self.ctx = ctx

HTML = 'html'
MD = 'md'
        
class EntryPage(Page):
    def __init__(self, ctx, dirpath, filename):
        Page.__init__(self, ctx)
        self.dirpath = dirpath
        self.filename = filename
        self.path = os.path.join(dirpath, filename)
        
        if filename.endswith('.html'):
            self.type = HTML
        elif filename.endswith('.md'):
            self.type = MD
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + filename)

from bloggor.excepts import RuntimeException
