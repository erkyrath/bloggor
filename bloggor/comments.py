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
        print('###', self.path)
        
    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.path)

    def read(self):
        pass
    
