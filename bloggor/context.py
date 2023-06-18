import os
import os.path
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bloggor.page import EntryPage, GenTemplatePage, StaticMDPage, TagListPage
import bloggor.jextension

class Context:
    def __init__(self, opts):
        self.opts = opts
        self.entriesdir = os.path.join(self.opts.srcdir, 'entries')
        
        self.pages = []
        self.entries = []
        
        self.jenv = Environment(
            loader = FileSystemLoader('templates'),
            extensions = [ bloggor.jextension.TagFilename ],
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
                self.entries.append(page)

        page = StaticMDPage(self, 'about.md', 'about.html')
        self.pages.append(page)

        page = GenTemplatePage(self, 'menu.html', 'menu.html')
        self.pages.append(page)

        page = TagListPage(self)
        self.pages.append(page)
    
        print('Building %d pages...' % (len(self.pages),))
        for page in self.pages:
            page.build()

        if self.opts.notemp:
            pass
        elif self.opts.nocommit:
            print('Skipping commit')   
        else:
            print('Committing %d pages...' % (len(self.pages),))
            for page in self.pages:
                page.commit()

        print('Done')
