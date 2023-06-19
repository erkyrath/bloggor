import os.path

class Page:
    def __init__(self, ctx):
        self.ctx = ctx
        self.jenv = ctx.jenv
        self.mdenv = ctx.mdenv

        self.outpath = None
        self.tempoutpath = None

    def complete(self):
        self.outdir = os.path.dirname(self.outpath)
        if not self.ctx.opts.notemp:
            self.tempoutpath = self.outpath + '_tmp.html'
        else:
            self.tempoutpath = self.outpath

    def commit(self):
        assert self.tempoutpath != self.outpath
        os.replace(os.path.join(self.ctx.opts.destdir, self.tempoutpath), os.path.join(self.ctx.opts.destdir, self.outpath))

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
            os.makedirs(os.path.join(self.ctx.opts.destdir, self.outdir), exist_ok=True)
            
        fl = open(os.path.join(self.ctx.opts.destdir, self.tempoutpath), 'w')
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
            os.makedirs(os.path.join(self.ctx.opts.destdir, self.outdir), exist_ok=True)
            
        fl = open(os.path.join(self.ctx.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('static.html')
        fl.write(template.render(title=self.title, body=self.body))
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
        
    def build(self):
        if self.outdir:
            os.makedirs(os.path.join(self.ctx.opts.destdir, self.outdir), exist_ok=True)
            
        fl = open(os.path.join(self.ctx.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('entry.html')
        fl.write(template.render(title=self.title, body=self.body, tags=self.tags))
        fl.close()


class TagListPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'tags.html'
        self.complete()

    def build(self):
        tags = [ (tag, len(ls)) for tag, ls in self.ctx.alltags.items() ]
        tags.sort()
        
        fl = open(os.path.join(self.ctx.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('tags.html')
        fl.write(template.render(title='All Tags', tags=tags))
        fl.close()


class TagListFreqPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'tags-freq.html'
        self.complete()

    def build(self):
        tags = [ (tag, len(ls)) for tag, ls in self.ctx.alltags.items() ]
        tags.sort(key=lambda tup:(-tup[1], tup[0]))
        
        fl = open(os.path.join(self.ctx.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('tags.html')
        fl.write(template.render(title='All Tags (by Frequency)', tags=tags))
        fl.close()


class TagPage(Page):
    def __init__(self, ctx, tag):
        Page.__init__(self, ctx)
        self.tag = tag
        self.outpath = os.path.join('tag', tagfilename(tag)+'.html')
        self.complete()

    def build(self):
        if self.outdir:
            os.makedirs(os.path.join(self.ctx.opts.destdir, self.outdir), exist_ok=True)
        
        entries = self.ctx.alltags[self.tag]
        
        fl = open(os.path.join(self.ctx.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('tag.html')
        fl.write(template.render(title='Tag: '+self.tag, tag=self.tag, entries=entries))
        fl.close()

from bloggor.excepts import RuntimeException
from bloggor.metafile import MetaFile
from bloggor.util import tagfilename
