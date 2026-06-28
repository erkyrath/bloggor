import os, os.path

from bloggor.pages import Page

class SongEntryPage(Page):
    def __init__(self, ctx, dirpath, filename):
        Page.__init__(self, ctx)
        self.dirpath = dirpath
        self.filename = filename

        self.path = os.path.join(self.dirpath, self.filename)
        
        if filename.endswith('.html'):
            self.type = FileType.HTML
            outfile = filename
        elif filename.endswith('.md'):
            self.type = FileType.MD
            outfile = filename[ : -3 ] + '.html'
        elif filename.endswith('.txt'):
            self.type = FileType.TXT
            outfile = filename[ : -4 ] + '.html'
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + filename)

        self.outpath = os.path.relpath(os.path.join(self.dirpath, outfile), start=ctx.entriesdir)
        if self.outpath.startswith('..') or self.outpath.startswith('/'):
            raise RuntimeException(self.path+': Bad outpath: ' + self.outpath)

        self.live = False
        self.title = None
        self.tags = None
        self.index = None
        self.fedipostid = None

        self.backdependpages = []

        self.complete()

    def __repr__(self):
        val = '' if self.live else ' DRAFT'
        return '<%s%s "%s">' % (self.__class__.__name__, val, self.outuri)

    def read(self):
        stat = os.stat(self.path)
        self.inmodtime = stat.st_mtime
        
        if self.type == FileType.HTML:
            mfl = MetaFile(self.path)
            body, metadata = mfl.read()
        elif self.type == FileType.TXT:
            mfl = MetaFile(self.path)
            body, metadata = mfl.read()
            val = str(markupsafe.escape(body))
            body = '<div class="PreWrapAll">\n%s</div>' % (val,)
        elif self.type == FileType.MD:
            fl = open(self.path)
            dat = fl.read()
            fl.close()
            self.mdenv.reset()
            body = self.mdenv.convert(dat)
            metadata = self.mdenv.Meta
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + self.type)

        self.body = body
        self.metadata = metadata

        self.excerpt = excerpthtml(body)

        self.title = None
        ls = metadata.get('title', None)
        if ls:
            self.title = ' '.join(ls)

        self.tags = []
        ls = metadata.get('tags', None)
        if ls:
            for val in ls:
                for tag in val.split(','):
                    tag = tag.strip().lower()
                    if tag:
                        self.tags.append(tag)

        if not self.title:
            raise RuntimeException(self.path+': No title')

        self.csslines = None
        ls = metadata.get('cssline', None)
        if ls:
            self.csslines = '\n'.join(ls)
        
        # self.index is set after all posts are read and sorted

        try:
            self.fedipostid = ls_as_value(metadata.get('fedipostid'))
        except ValueError as ex:
            raise RuntimeException(self.path+': Fedipostid not valid: '+str(ex))
        
        try:
            self.live = ls_as_bool(metadata.get('live'))
        except ValueError as ex:
            raise RuntimeException(self.path+': Live not valid: '+str(ex))

        if not self.live:
            return

    def build(self):
        preventry = None
        nextentry = None
        if self.live and self.index > 0:
            preventry = self.ctx.liveentries[self.index-1]
        if self.live and self.index < len(self.ctx.liveentries)-1:
            nextentry = self.ctx.liveentries[self.index+1]

        fl = self.openwrite()
        template = self.jenv.get_template('entry.html')
        fl.write(template.render(
            entry=self,
            title=self.title,
            nextentry=nextentry,
            preventry=preventry))
        fl.close()

from bloggor.constants import FileType
from bloggor.excepts import RuntimeException
from bloggor.metafile import MetaFile, ls_as_bool, ls_as_value
from bloggor.util import excerpthtml
