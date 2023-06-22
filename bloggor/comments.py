import os
import os.path
import markdown

HTML = 'html'
WHTML = 'whtml'
MD = 'md'
TXT = 'txt'

class CommentThread:
    def __init__(self, ctx, dirpath, filename):
        self.dirpath = dirpath
        self.filename = filename
        assert filename.endswith('.comments')

        self.path = os.path.join(self.dirpath, self.filename)
        self.outpath = os.path.relpath(self.path, start=ctx.entriesdir)
        self.outuri = self.outpath[ : -9]
        
    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.outuri)

    def read(self):
        pass
    
