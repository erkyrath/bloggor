import os.path

class Page:
    def __init__(self, ctx):
        self.ctx = ctx
        self.jenv = ctx.jenv
        self.mdenv = ctx.mdenv

        self.outpath = None

    def commit(self):
        os.replace(os.path.join(self.ctx.opts.destdir, self.tempoutpath), os.path.join(self.ctx.opts.destdir, self.outpath))

class StaticMDPage(Page):
    def __init__(self, ctx, filename, outpath):
        Page.__init__(self, ctx)
        self.dirpath = os.path.join(ctx.opts.srcdir, 'pages')
        self.filename = filename
        self.outpath = outpath
        self.tempoutpath = self.outpath + '_tmp.html'

        self.path = os.path.join(self.dirpath, self.filename)
        self.outdir = os.path.dirname(self.outpath)

    def __repr__(self):
        return '<StaticMDPage "%s">' % (self.filename,)
        
    def build(self):
        fl = open(self.path)
        dat = fl.read()
        fl.close()
        self.mdenv.reset()
        body = self.mdenv.convert(dat)

        if self.outdir:
            os.makedirs(os.path.join(self.ctx.opts.destdir, self.outdir), exist_ok=True)
            
        fl = open(os.path.join(self.ctx.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('page.html')
        fl.write(template.render(title='Zarf Updates', body=body))
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
        self.outdir = os.path.dirname(self.outpath)
        self.tempoutpath = self.outpath + '_tmp.html'

    def __repr__(self):
        return '<EntryPage "%s">' % (self.path,)
        
    def build(self):
        if self.type == HTML:
            fl = open(self.path)
            dat = fl.read()
            fl.close()
            body = dat
        else:
            fl = open(self.path)
            dat = fl.read()
            fl.close()
            self.mdenv.reset()
            body = self.mdenv.convert(dat)

        if self.outdir:
            os.makedirs(os.path.join(self.ctx.opts.destdir, self.outdir), exist_ok=True)
            
        fl = open(os.path.join(self.ctx.opts.destdir, self.tempoutpath), 'w')
        template = self.jenv.get_template('page.html')
        fl.write(template.render(title='Zarf Updates', body=body))
        fl.close()


from bloggor.excepts import RuntimeException
