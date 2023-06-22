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

        for ix, tup in enumerate(ls):
            body, meta = tup
            self.comments.append(Comment(self.ctx, self, ix, body, meta))

        self.entry.comments = self.comments

class Comment:
    def __init__(self, ctx, thread, index, body, meta):
        self.thread = thread
        self.id = '%s[%d]' % (thread.outuri, index,)

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
            raise RuntimeException(self.id+': unknown comment format: '+format)

        self.authorname = None
        self.authoruri = None
        self.depth = 0

        ls = meta.get('depth', None)
        if ls:
            try:
                self.depth = int(ls[0])
            except:
                raise RuntimeException(self.id+': Depth must be a number: ' + ''.join(ls))
            
        ls = meta.get('authorname', None)
        if ls:
            self.authorname = ' '.join(ls)
        ls = meta.get('authoruri', None)
        if ls:
            self.authoruri = ' '.join(ls)

        ls = meta.get('published')
        if not ls:
            raise RuntimeException(self.id+': No published date')
        val = ''.join(ls)
        try:
            self.published = parsedate(val)
        except ValueError:
            raise RuntimeException(self.id+': Invalid published date: '+val)

    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.id)


from bloggor.metafile import MultiMetaFile
from bloggor.excepts import RuntimeException
from bloggor.util import parsedate
