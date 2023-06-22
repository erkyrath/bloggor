import os
import os.path
import markdown
import markupsafe

HTML = 'html'
WHTML = 'whtml'
MD = 'md'
TXT = 'txt'

class CommentThread:
    def __init__(self, ctx, dirpath, filename):
        self.ctx = ctx
        self.dirpath = dirpath
        self.filename = filename
        assert filename.endswith('.comments')

        self.path = os.path.join(self.dirpath, self.filename)
        self.outpath = os.path.relpath(self.path, start=ctx.entriesdir)
        self.outuri = self.outpath[ : -9]
        self.entry = None
        self.comments = []
        
    def __repr__(self):
        return '<%s "%s" (%d)>' % (self.__class__.__name__, self.outuri, len(self.comments))

    def read(self):
        mfl = MultiMetaFile(self.path)
        ls = mfl.read()

        for body, meta in ls:
            self.comments.append(Comment(self.ctx, self, body, meta))

class Comment:
    def __init__(self, ctx, thread, body, meta):
        self.thread = thread

        body = body.rstrip() + '\n'

        format = meta.get('format')
        if not format:
            format = TXT
        else:
            format = ''.join(format)
            if format == 'text':
                format = TXT
            
        if format == TXT:
            self.body = str(markupsafe.escape(body))
        elif format == HTML:
            self.body = body
        elif format == WHTML:
            self.body = '<div class="PreWrapAll">\n%s</div>' % (body,)
        elif format == MD:
            ctx.mdenv.reset()
            self.body = ctx.mdenv.convert(body)
        else:
            raise RuntimeException(thread.outuri+': unknown comment format: '+format)

            
from bloggor.metafile import MultiMetaFile
from bloggor.excepts import RuntimeException

    
