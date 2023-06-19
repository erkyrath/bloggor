import os
import os.path
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bloggor.util import MultiDict
from bloggor.pages import FrontPage
from bloggor.pages import EntryPage, GenTemplatePage, StaticMDPage
from bloggor.pages import TagListPage, TagListFreqPage, TagPage
from bloggor.pages import RecentEntriesPage, YearEntriesPage
import bloggor.jextension
import bloggor.mdextension

class Context:
    def __init__(self, opts):
        self.opts = opts
        self.entriesdir = os.path.join(self.opts.srcdir, 'entries')
        
        self.pages = []
        self.entries = []
        self.entriesbytag = {}
        self.entriesbyyear = MultiDict()
        self.recentfew = []
        
        self.jenv = Environment(
            loader = FileSystemLoader('templates'),
            extensions = [ bloggor.jextension.TagFilename, bloggor.jextension.SplitAtMore ],
            autoescape = select_autoescape(),
            keep_trailing_newline = True,
        )

        self.mdenv = markdown.Markdown(extensions=['meta', 'def_list', 'fenced_code', 'tables', bloggor.mdextension.MoreBreakExtension()])

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

        # Preliminary, we'll resort when we have all the data
        self.entries.sort(key=lambda entry:(entry.path))
        
        page = StaticMDPage(self, 'about.md', 'about.html')
        self.pages.append(page)

        page = GenTemplatePage(self, 'menu.html', 'menu.html')
        self.pages.append(page)

        print('Reading %d pages...' % (len(self.pages),))
        for page in self.pages:
            page.read()
                    
        self.entries.sort(key=lambda entry:(entry.draft, entry.published, entry.title))
        for ix in range(len(self.entries)):
            self.entries[ix].index = ix

        self.recentfew = self.entries[ -3 : ]
        self.recentfew.reverse()

        self.recententries = self.entries[ -10 : ]
        self.recententries.reverse()

        for entry in self.entries:
            self.entriesbyyear.add(entry.year, entry)
            for tag in entry.tags:
                if tag not in self.entriesbytag:
                    self.entriesbytag[tag] = [ entry ]
                else:
                    self.entriesbytag[tag].append(entry)

        page = FrontPage(self)
        self.pages.append(page)

        page = RecentEntriesPage(self)
        self.pages.append(page)

        for year in self.entriesbyyear:
            page = YearEntriesPage(self, year)
            self.pages.append(page)
        
        page = TagListPage(self)
        self.pages.append(page)

        page = TagListFreqPage(self)
        self.pages.append(page)

        for tag in self.entriesbytag:
            page = TagPage(self, tag)
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
