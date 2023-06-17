import os
import os.path
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bloggor.page import EntryPage, StaticMDPage

class Context:
    def __init__(self, opts):
        self.opts = opts
        self.pages = []
        
        self.jenv = Environment(
            loader = FileSystemLoader('templates'),
            autoescape = select_autoescape(),
            keep_trailing_newline = True,
        )

        self.mdenv = markdown.Markdown(extensions=['meta', 'def_list', 'fenced_code', 'tables'])

    def build(self):
        print('Reading...')
        for dirpath, dirnames, filenames in os.walk(os.path.join(self.opts.srcdir, 'entries')):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                if filename.endswith('~'):
                    continue
                print(dirpath, filename)
                page = EntryPage(self, dirpath, filename)
                self.pages.append(page)

        page = StaticMDPage(self, 'home.md')
        self.pages.append(page)
    
        print('Building...')
        for page in self.pages:
            page.build()

        print('Done')
