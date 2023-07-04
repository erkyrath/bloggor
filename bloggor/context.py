import os
import os.path
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bloggor.constants import FeedType
from bloggor.excepts import RuntimeException
from bloggor.util import MultiDict
from bloggor.pages import FrontPage
from bloggor.pages import EntryPage, GenTemplatePage, StaticPage
from bloggor.pages import TagListPage, TagListFreqPage, TagPage
from bloggor.pages import RecentEntriesPage, YearEntriesPage
from bloggor.pages import HistoryPage
from bloggor.pages import FeedPage
from bloggor.comments import CommentThread
import bloggor.jextension
import bloggor.mdextension

class Context:
    def __init__(self, opts):
        self.opts = opts
        self.entriesdir = os.path.join(self.opts.srcdir, 'entries')
        self.pagesdir = os.path.join(self.opts.srcdir, 'pages')

        self.errors = None
        
        self.pages = []
        self.entries = []
        self.commentthreads = []
        self.entriesbyuri = {}

        self.liveentries = []
        self.draftentries = []
        
        # These are only live entries.
        self.entriesbytag = {}
        self.entriesbyyear = MultiDict()
        self.entriesbymonth = MultiDict()
        self.recentyears = []
        self.recententries = []
        self.recentfew = []
        
        self.jenv = Environment(
            loader = FileSystemLoader(os.path.join(self.opts.srcdir, 'templates')),
            extensions = [
                bloggor.jextension.TagFilename,
                bloggor.jextension.SplitAtMore,
                bloggor.jextension.CommentDepthStep,
            ],
            autoescape = select_autoescape(),
            keep_trailing_newline = True,
        )
        self.jenv.globals['serverurl'] = opts.serverurl
        self.jenv.globals['fediserver'] = 'mastodon.gamedev.place'
        self.jenv.globals['fediuser'] = 'zarfeblong'
        self.jenv.globals['blogctx'] = self

        self.mdenv = markdown.Markdown(extensions=[
            'meta', 'attr_list', 'def_list', 'fenced_code', 'tables',
            bloggor.mdextension.MoreBreakExtension(),
            bloggor.mdextension.UnwrapExtension(),
            bloggor.mdextension.LocalLinkExtension(),
        ])

    def run(self, pagespecs=None):
        self.errors = []

        self.readsrc()
        if self.errors:
            return False

        self.addnonsrc()
        if self.errors:
            return False

        if self.opts.dryrun:
            return True

        if not pagespecs:
            pagelist = list(self.pages)
        else:
            pagespecs = [ spec[1:] if spec.startswith('/') else spec for spec in pagespecs ]
            pagelist = [ page for page in self.pages if page.match(pagespecs) ]
            if not pagelist:
                print('No pages match')
                return False
    
        self.build(pagelist)

        return True

    def readsrc(self):
        for dirpath, dirnames, filenames in os.walk(self.entriesdir):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                if filename.endswith('~'):
                    continue
                if filename.endswith('.json'):
                    continue
                try:
                    if filename.endswith('.html') or filename.endswith('.md'):
                        page = EntryPage(self, dirpath, filename)
                        self.pages.append(page)
                        self.entries.append(page)
                        self.entriesbyuri[page.outuri] = page
                        continue
                    if filename.endswith('.comments'):
                        com = CommentThread(self, dirpath, filename)
                        self.commentthreads.append(com)
                        continue
                    raise RuntimeException('unrecognized file type: '+filename)
                except RuntimeException as ex:
                    print('Error: %s' % (ex,))
                    self.errors.append(ex)

        for dirpath, dirnames, filenames in os.walk(self.pagesdir):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                if filename.endswith('~'):
                    continue
                try:
                    if filename.endswith('.html') or filename.endswith('.md'):
                        page = StaticPage(self, dirpath, filename)
                        self.pages.append(page)
                        continue
                    raise RuntimeException('unrecognized file type: '+filename)
                except RuntimeException as ex:
                    print('Error: %s' % (ex,))
                    self.errors.append(ex)

        if self.errors:
            return

        # Preliminary, we'll resort when we have all the data
        self.entries.sort(key=lambda entry:(entry.path))

        for comt in self.commentthreads:
            try:
                if comt.outuri not in self.entriesbyuri:
                    raise RuntimeException('comments file has no entry: '+comt.outuri)
                ent = self.entriesbyuri[comt.outuri]
                ent.commentthread = comt
                comt.entry = ent
            except RuntimeException as ex:
                print('Error: %s' % (ex,))
                self.errors.append(ex)
        
        if self.errors:
            return

        print('Reading %d pages...' % (len(self.pages),))
        for page in self.pages:
            try:
                page.read()
            except RuntimeException as ex:
                print('Error: %s' % (ex,))
                self.errors.append(ex)

        print('Reading %d comment threads...' % (len(self.commentthreads),))
        for comt in self.commentthreads:
            try:
                comt.read()
            except RuntimeException as ex:
                print('Error: %s' % (ex,))
                self.errors.append(ex)

        if self.errors:
            return

        for page in self.entries:
            if page.live:
                self.liveentries.append(page)
            else:
                self.draftentries.append(page)

        self.draftentries.sort(key=lambda entry:entry.outuri)
                
        self.liveentries.sort(key=lambda entry:(entry.published, entry.title))
        for ix in range(len(self.liveentries)):
            self.liveentries[ix].index = ix

        self.recentfew = self.liveentries[ -4 : ]
        self.recentfew.reverse()

        self.recententries = self.liveentries[ -10 : ]
        self.recententries.reverse()

        for entry in self.liveentries:
            self.entriesbyyear.add(entry.year, entry)
            self.entriesbymonth.add(entry.shortmonth, entry)
            for tag in entry.tags:
                if tag not in self.entriesbytag:
                    self.entriesbytag[tag] = [ entry ]
                else:
                    self.entriesbytag[tag].append(entry)

        ls = list(self.entriesbyyear.keys())
        ls.sort(reverse=True)
        self.recentyears = ls[ : 5 ]
        
    def addnonsrc(self):
        page = FrontPage(self)
        self.pages.append(page)

        page = GenTemplatePage(self, 'menu.html', 'menu.html')
        self.pages.append(page)

        page = HistoryPage(self)
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

        page = FeedPage(self, FeedType.ATOM, 'feeds/posts/default.xml')
        self.pages.append(page)

        page = FeedPage(self, FeedType.RSS, 'feeds/posts/default.rss', withsuffix=True)
        self.pages.append(page)

    def build(self, pagelist):
        print('Building %d pages...' % (len(pagelist),))
        if len(pagelist) < 20:
            for page in pagelist:
                print('  .../'+page.outpath)
                
        for page in pagelist:
            page.build()

        ls = [ page.outpath for page in pagelist ]
        assert len(ls) == len(set(ls))

        if self.opts.notemp:
            pass
        elif self.opts.nocommit:
            print('Skipping commit')   
        else:
            ls = [ page.tempoutpath for page in pagelist ]
            assert len(ls) == len(set(ls))
            
            print('Committing %d pages...' % (len(pagelist),))
            for page in pagelist:
                page.commit()

        for page in self.draftentries:
            print('Draft: %s%s' % (self.opts.serverurl, page.outuri,))
