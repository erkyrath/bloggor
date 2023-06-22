import os
import os.path
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bloggor.excepts import RuntimeException
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
            loader = FileSystemLoader(os.path.join(self.opts.srcdir, 'templates')),
            extensions = [
                bloggor.jextension.TagFilename,
                bloggor.jextension.SplitAtMore
            ],
            autoescape = select_autoescape(),
            keep_trailing_newline = True,
        )
        self.jenv.globals['serverurl'] = opts.serverurl

        self.mdenv = markdown.Markdown(extensions=[
            'meta', 'attr_list', 'def_list', 'fenced_code', 'tables',
            bloggor.mdextension.MoreBreakExtension(),
            bloggor.mdextension.UnwrapExtension(),
            bloggor.mdextension.LocalLinkExtension(),
        ])

    def build(self):
        for dirpath, dirnames, filenames in os.walk(self.entriesdir):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                if filename.endswith('~'):
                    continue
                if filename.endswith('.comments') or filename.endswith('.json'):
                    continue
                if filename.endswith('.html') or filename.endswith('.md'):
                    page = EntryPage(self, dirpath, filename)
                    self.pages.append(page)
                    self.entries.append(page)
                    continue
                raise RuntimeException('unrecognized filename: '+filename)

        # Preliminary, we'll resort when we have all the data
        self.entries.sort(key=lambda entry:(entry.path))
        
        page = StaticMDPage(self, 'about.md', 'about.html')
        self.pages.append(page)

        page = GenTemplatePage(self, 'menu.html', 'menu.html')
        self.pages.append(page)

        print('reading %d pages...' % (len(self.pages),))
        errors = []
        for page in self.pages:
            try:
                page.read()
            except RuntimeException as ex:
                print('Error: %s' % (ex,))
                errors.append(ex)

        if errors:
            return False
                    
        self.entries.sort(key=lambda entry:(entry.draft, entry.published, entry.title))
        for ix in range(len(self.entries)):
            self.entries[ix].index = ix

        self.recentfew = self.entries[ -4 : ]
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

        if self.opts.dryrun:
            return True
    
        print('building %d pages...' % (len(self.pages),))
        for page in self.pages:
            page.build()

        if self.opts.notemp:
            pass
        elif self.opts.nocommit:
            print('skipping commit')   
        else:
            print('committing %d pages...' % (len(self.pages),))
            for page in self.pages:
                page.commit()

        print('done')
        return True
