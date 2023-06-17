import os.path

class Page:
    def __init__(self, ctx):
        self.ctx = ctx
        self.jenv = ctx.jenv
        self.mdenv = ctx.mdenv

class StaticMDPage:
    def __init__(self, ctx, filename):
        Page.__init__(self, ctx)
        self.dirpath = os.path.join(ctx.opts.srcdir, 'pages')
        self.filename = filename

        self.path = os.path.join(self.dirpath, self.filename)

    def build(self):
        fl = open(self.path)
        dat = fl.read()
        fl.close()
        self.mdenv.reset()
        body = self.mdenv.convert(dat)

        fl = open(os.path.join(self.ctx.opts.destdir, 'index.html'), 'w')
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
        elif filename.endswith('.md'):
            self.type = MD
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + filename)

    def build(self):
        pass

from bloggor.excepts import RuntimeException
