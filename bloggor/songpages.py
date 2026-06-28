import os, os.path

from bloggor.pages import Page

class SongFrontPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'index.html'
        self.frequent = True
        self.backdependpages = [ (page, Depend.ALL) for page in ctx.liveentries ]
        self.complete()

    def build(self):
        fl = self.openwrite()
        template = self.jenv.get_template('front.html')
        fl.write(template.render(
            title=None,
            entries=self.ctx.liveentries))
        fl.close()


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

        self.title = None
        self.tags = None
        self.index = None
        self.fedipostid = None

        self.backdependpages = []

        self.complete()

    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.outuri)

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

    def build(self):
        fl = self.openwrite()
        template = self.jenv.get_template('entry.html')
        fl.write(template.render(
            entry=self,
            title=self.title))
        fl.close()

from bloggor.constants import FileType, Depend
from bloggor.excepts import RuntimeException
from bloggor.metafile import MetaFile, ls_as_bool, ls_as_value
from bloggor.util import excerpthtml
