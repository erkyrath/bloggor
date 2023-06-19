import os.path
import datetime

class Page:
    def __init__(self, ctx):
        self.ctx = ctx
        self.opts = ctx.opts
        self.jenv = ctx.jenv
        self.mdenv = ctx.mdenv

        self.outpath = None
        self.tempoutpath = None

    def complete(self):
        self.outdir = os.path.dirname(self.outpath)
        if not self.opts.notemp:
            self.tempoutpath = self.outpath + '_tmp.html'
        else:
            self.tempoutpath = self.outpath

    def commit(self):
        assert self.tempoutpath != self.outpath
        os.replace(os.path.join(self.opts.destdir, self.tempoutpath), os.path.join(self.opts.destdir, self.outpath))

    def read(self):
        raise Exception(repr(self)+': read() not implemented')

    def build(self):
        raise Exception(repr(self)+': build() not implemented')


class GenTemplatePage(Page):
    def __init__(self, ctx, template, outpath):
        Page.__init__(self, ctx)
        self.template = template
        self.outpath = outpath

        self.complete()

    def __repr__(self):
        return '<GenTemplatePage "%s">' % (self.template,)

    def read(self):
        pass
        
    def build(self):
        if self.outdir:
            os.makedirs(os.path.join(self.opts.destdir, self.outdir), exist_ok=True)
            
        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template(self.template)
        fl.write(template.render())
        fl.close()

        
class StaticMDPage(Page):
    def __init__(self, ctx, filename, outpath):
        Page.__init__(self, ctx)
        self.dirpath = os.path.join(ctx.opts.srcdir, 'pages')
        self.filename = filename
        self.outpath = outpath

        self.path = os.path.join(self.dirpath, self.filename)

        self.complete()

    def __repr__(self):
        return '<StaticMDPage "%s">' % (self.filename,)
        
    def read(self):
        fl = open(self.path)
        dat = fl.read()
        fl.close()
        self.mdenv.reset()
        self.body = self.mdenv.convert(dat)
        self.metadata = self.mdenv.Meta

        self.title = None
        ls = self.metadata.get('title', None)
        if ls:
            self.title = ' '.join(ls)

    def build(self):
        if self.outdir:
            os.makedirs(os.path.join(self.opts.destdir, self.outdir), exist_ok=True)
            
        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('static.html')
        fl.write(template.render(
            title=self.title,
            body=self.body))
        fl.close()


class RecentEntriesPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'recent.html'
        self.complete()

    def build(self):
        entries = self.ctx.entries[ -20 : ]
        entries.reverse()
        
        yearls = list(self.ctx.entriesbyyear.keys())
        yearls.sort(reverse=True)

        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('recent.html')
        fl.write(template.render(
            title='Recent Posts',
            entries=entries,
            years=yearls))
        fl.close()
        
    
class YearEntriesPage(Page):
    def __init__(self, ctx, year):
        Page.__init__(self, ctx)
        self.year = year
        self.outpath = 'year-%d.html' % (self.year,)
        self.complete()

    def build(self):
        entries = self.ctx.entriesbyyear[self.year]

        yearls = list(self.ctx.entriesbyyear.keys())
        yearls.sort(reverse=True)

        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('recent.html')
        fl.write(template.render(
            title='Posts From %d' % (self.year,),
            year=self.year,
            entries=entries,
            years=yearls))
        fl.close()
        
    
class TagListPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'tags.html'
        self.complete()

    def build(self):
        tags = [ (tag, len(ls)) for tag, ls in self.ctx.entriesbytag.items() ]
        tags.sort()
        
        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('tags.html')
        fl.write(template.render(
            title='All Tags (Alphabetical)',
            tags=tags,
            sortby='alpha'))
        fl.close()


class TagListFreqPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'tags-freq.html'
        self.complete()

    def build(self):
        tags = [ (tag, len(ls)) for tag, ls in self.ctx.entriesbytag.items() ]
        tags.sort(key=lambda tup:(-tup[1], tup[0]))
        
        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('tags.html')
        fl.write(template.render(
            title='All Tags (by Frequency)',
            tags=tags,
            sortby='freq'))
        fl.close()


class TagPage(Page):
    def __init__(self, ctx, tag):
        Page.__init__(self, ctx)
        self.tag = tag
        self.outpath = os.path.join('tag', tagfilename(tag)+'.html')
        self.complete()

    def build(self):
        if self.outdir:
            os.makedirs(os.path.join(self.opts.destdir, self.outdir), exist_ok=True)
        
        entries = self.ctx.entriesbytag[self.tag]
        oneentry = (len(entries) == 1)
        
        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('tag.html')
        fl.write(template.render(
            title='Tag: '+self.tag,
            tag=self.tag,
            entries=entries,
            oneentry=oneentry))
        fl.close()


HTML = 'html'
MD = 'md'
        
class EntryPage(Page):
    def __init__(self, ctx, dirpath, filename):
        Page.__init__(self, ctx)
        self.dirpath = dirpath
        self.filename = filename

        self.path = os.path.join(self.dirpath, self.filename)
        
        if filename.endswith('.html'):
            self.type = HTML
            outfile = filename
        elif filename.endswith('.md'):
            self.type = MD
            outfile = filename[ : -3 ] + '.html'
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + filename)

        self.outpath = os.path.relpath(os.path.join(self.dirpath, outfile), start=ctx.entriesdir)
        if self.outpath.startswith('..') or self.outpath.startswith('/'):
            raise RuntimeException(self.path+': Bad outpath: ' + self.outpath)

        self.title = None
        self.tags = None
        self.index = None
        self.complete()

    def __repr__(self):
        return '<EntryPage "%s">' % (self.path,)

    def read(self):
        if self.type == HTML:
            mfl = MetaFile(self.path)
            body, metadata = mfl.read()
        else:
            fl = open(self.path)
            dat = fl.read()
            fl.close()
            self.mdenv.reset()
            body = self.mdenv.convert(dat)
            metadata = self.mdenv.Meta

        self.body = body
        self.metadata = metadata

        self.title = None
        ls = metadata.get('title', None)
        if ls:
            self.title = ' '.join(ls)

        ls = metadata.get('published')
        if not ls:
            raise RuntimeException(self.path+': No published date')
        val = ''.join(ls)
        self.published = parsedate(val)
        if not self.published:
            raise RuntimeException(self.path+': Invalid published date: '+val)

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

        # self.index is set after all posts are read and sorted
        
        self.draft = False  ###
        ### What is the following for drafts? Current date? End of the given month?

        self.shortdate = self.published[0:10]
        self.year = int(self.shortdate[0:4])
        val = datetime.date.fromisoformat(self.shortdate)
        self.longpublished = val.strftime('%A, %B %d, %Y').replace(' 0', ' ')

        val = self.shortdate[0:7].replace('-', '/')
        if val != self.outdir:
            raise RuntimeException(self.path+': Published date does not match directory: ' + self.shortdate)

        
    def build(self):
        if self.outdir:
            os.makedirs(os.path.join(self.opts.destdir, self.outdir), exist_ok=True)

        preventry = None
        nextentry = None
        if self.index > 0:
            preventry = self.ctx.entries[self.index-1]
        if self.index < len(self.ctx.entries)-1:
            nextentry = self.ctx.entries[self.index+1]
            
        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('entry.html')
        fl.write(template.render(
            entry=self,
            title=self.title,
            nextentry=nextentry,
            preventry=preventry))
        fl.close()


from bloggor.excepts import RuntimeException
from bloggor.metafile import MetaFile
from bloggor.util import tagfilename, parsedate
