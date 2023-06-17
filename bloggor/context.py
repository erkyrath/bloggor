import os
import os.path
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bloggor.page import EntryPage, StaticMDPage

class Context:
    def __init__(self, opts):
        self.opts = opts
        self.entriesdir = os.path.join(self.opts.srcdir, 'entries')
        
        self.pages = []
        
        self.jenv = Environment(
            loader = FileSystemLoader('templates'),
            autoescape = select_autoescape(),
            keep_trailing_newline = True,
        )

        self.mdenv = markdown.Markdown(extensions=['meta', 'def_list', 'fenced_code', 'tables'])

    def build(self):
        print('Reading...')
        for dirpath, dirnames, filenames in os.walk(self.entriesdir):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                if filename.endswith('~'):
                    continue
                page = EntryPage(self, dirpath, filename)
                self.pages.append(page)

        page = StaticMDPage(self, 'home.md', 'index.html')
        self.pages.append(page)
    
        print('Building %d pages...' % (len(self.pages),))
        for page in self.pages:
            page.build()

        if not self.opts.nocommit:
            print('Committing %d pages...' % (len(self.pages),))
            for page in self.pages:
                page.commit()
        else:
             print('Skipping commit')   

        print('Done')
