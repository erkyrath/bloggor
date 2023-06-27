import os
import os.path
import datetime
import markdown
import markupsafe

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
        self.latestpublished = None
        self.longlatestpublished = None
        self.shortlatestpublished = None
        
    def __repr__(self):
        return '<%s "%s" (%d)>' % (self.__class__.__name__, self.outuri, len(self.comments))

    def read(self):
        mfl = MultiMetaFile(self.path)
        ls = mfl.read()

        for ix, mf in enumerate(ls):
            body, meta = mf.read()
            self.comments.append(Comment(self.ctx, self, ix, body, meta))

        publs = [ com.published for com in self.comments if com.published ]
        if publs and self.entry.published:
            self.latestpublished = max(publs)
            self.longlatestpublished = relativetime(self.latestpublished, self.entry.published)
            self.shortlatestpublished = relativetime(self.latestpublished, self.entry.published, english=False)

        self.entry.comments = self.comments

class Comment:
    def __init__(self, ctx, thread, index, body, meta):
        self.thread = thread
        self.id = '%s[%d]' % (thread.outuri, index,)

        body = body.rstrip() + '\n'

        format = meta.get('format')
        if not format:
            format = constants.TXT
        else:
            format = ''.join(format)
            if format == 'text':
                format = constants.TXT
            
        if format == constants.TXT:
            val = str(markupsafe.escape(body))
            self.body = '<div class="PreWrapAll">\n%s</div>' % (val,)
        elif format == constants.HTML:
            self.body = body
        elif format == constants.WHTML:
            self.body = '<div class="PreWrapAll">\n%s</div>' % (body,)
        elif format == constants.MD:
            ctx.mdenv.reset()
            self.body = ctx.mdenv.convert(body)
        else:
            raise RuntimeException(self.id+': unknown comment format: '+format)

        self.source = None
        self.authorname = None
        self.authoruri = None
        self.depth = 0

        ls = meta.get('depth', None)
        if ls:
            try:
                self.depth = int(ls[0])
            except:
                raise RuntimeException(self.id+': Depth must be a number: ' + ''.join(ls))
            
        ls = meta.get('source', None)
        if ls:
            self.source = ''.join(ls)
            
        ls = meta.get('authorname', None)
        if ls:
            self.authorname = ' '.join(ls)
        ls = meta.get('authoruri', None)
        if ls:
            self.authoruri = ' '.join(ls)

        try:
            val = ls_as_value(meta.get('published'))
        except ValueError as ex:
            raise RuntimeException(self.id+': Invalid published date: '+str(ex))
        if val is None:
            raise RuntimeException(self.id+': No published date')
        try:
            self.publishedraw = parsedate(val)
            self.published = datetime.datetime.fromisoformat(self.publishedraw)
        except ValueError:
            raise RuntimeException(self.id+': Invalid published date: '+val)

        if self.source == 'gameshelf':
            self.sourcename = 'imported from Gameshelf'
        elif self.source == 'blogger':
            self.sourcename = 'imported from Blogger'
        elif self.source == 'mastodon':
            self.sourcename = 'from Mastodon'
        elif self.source == 'zarf':
            self.sourcename = 'from Zarf'
        else:
            self.sourcename = None

        publocal = self.published.astimezone(constants.eastern_tz)
        self.longpublished = publocal.strftime('%B %d, %Y at %I:%M %p').replace(' 0', ' ')

    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.id)


from bloggor import constants
from bloggor.metafile import MultiMetaFile, ls_as_value
from bloggor.excepts import RuntimeException
from bloggor.util import parsedate, relativetime

