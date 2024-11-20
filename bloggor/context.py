import os
import os.path
import time
import configparser
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bloggor.constants import FeedType, Depend
from bloggor.excepts import RuntimeException
from bloggor.util import MultiDict
from bloggor.util import parsespecs, parsedate, parseinterval
from bloggor.util import xofypages
from bloggor.util import urltohost
from bloggor.pages import FrontPage
from bloggor.pages import EntryPage, GenTemplatePage, StaticPage
from bloggor.pages import TagListPage, TagListFreqPage, TagPage
from bloggor.pages import RecentEntriesPage, YearEntriesPage, MonthEntriesPage
from bloggor.pages import HistoryPage
from bloggor.pages import FeedPage
from bloggor.pages import PageSet
from bloggor.comments import CommentThread
import bloggor.jextension
import bloggor.mdextension

class Context:
    def __init__(self, opts):
        self.opts = opts
        
        self.config = self.readconfig()
        self.serverurl = self.config['serverurl']
        
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
        self.entriesbytag = MultiDict()
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
        self.jenv.globals['blogctx'] = self
        self.jenv.globals['serverurl'] = self.serverurl
        self.jenv.globals['servername'] = urltohost(self.serverurl)
        self.jenv.globals['blogtitle'] = self.config['blogtitle']
        self.jenv.globals['blogsubtitle'] = self.config['blogsubtitle']
        self.jenv.globals['ownername'] = self.config['ownername']
        self.jenv.globals['fediserver'] = self.config['fediserver']
        self.jenv.globals['fediuser'] = self.config['fediuser']

        self.mdenv = markdown.Markdown(extensions=[
            'meta', 'attr_list', 'def_list', 'fenced_code', 'tables',
            bloggor.mdextension.StrikethroughExtension(),
            bloggor.mdextension.MoreBreakExtension(),
            bloggor.mdextension.UnwrapExtension(),
            bloggor.mdextension.DictDefInlineExtension(),
            bloggor.mdextension.LocalLinkExtension(self.serverurl),
        ])

    def readconfig(self):
        configpath = self.opts.configfile
        if not configpath:
            configpath = os.path.join(self.opts.srcdir, 'bloggor.cfg')

        defaults = {
            'blogtitle': 'Blog',
            'blogsubtitle': 'Some words',
            'ownername': 'Owner',
            'serverurl': 'https://blog.example.com/',
            'fediuser': 'username',
            'fediserver': 'mastodon.example.com',
        }
        config = configparser.ConfigParser(defaults=defaults)

        config.read(configpath)
        if 'bloggor' in config:
            return config['bloggor']
        else:
            return config['DEFAULT']

    def run(self, pagespecs=None):
        self.errors = []

        self.readsrc()
        if self.errors:
            return False

        self.addnonsrc()
        if self.errors:
            return False

        pagelist = self.filterpages(pagespecs)
        if not pagelist:
            return True
    
        if self.opts.dryrun:
            print('Not building %s...' % (xofypages(len(pagelist), len(self.pages)),))
            if len(pagelist) < 20 or self.opts.longlist:
                for page in pagelist:
                    print('  .../'+page.outpath)
            return True

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
                if filename.endswith('.notes'):
                    continue
                try:
                    if filename.endswith('.html') or filename.endswith('.md') or filename.endswith('.txt'):
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
                    if filename.endswith('.html') or filename.endswith('.md') or filename.endswith('.txt'):
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

        print('Reading %d entries plus %d pages...' % (len(self.entries), len(self.pages)-len(self.entries),))
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
        for ix, page in enumerate(self.liveentries):
            page.index = ix
            if ix > 0:
                self.liveentries[ix-1].backdependpages.append( (page, Depend.TITLE|Depend.CREATED) )
            if ix < len(self.liveentries)-1:
                self.liveentries[ix+1].backdependpages.append( (page, Depend.TITLE|Depend.CREATED) )

        self.recentfew = self.liveentries[ -4 : ]
        self.recentfew.reverse()

        self.recententries = self.liveentries[ -10 : ]
        self.recententries.reverse()

        for entry in self.liveentries:
            self.entriesbyyear.add(entry.year, entry)
            self.entriesbymonth.add(entry.shortmonth, entry)
            for tag in entry.tags:
                self.entriesbytag.add(tag, entry)

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

        for year, ls in self.entriesbyyear.items():
            page = YearEntriesPage(self, year, ls)
            self.pages.append(page)
        
        for month, ls in self.entriesbymonth.items():
            page = MonthEntriesPage(self, month, ls)
            self.pages.append(page)
        
        page = TagListPage(self)
        self.pages.append(page)

        page = TagListFreqPage(self)
        self.pages.append(page)

        for tag, ls in self.entriesbytag.items():
            page = TagPage(self, tag, ls)
            self.pages.append(page)

        page = FeedPage(self, FeedType.ATOM, 'feeds/posts/default.xml')
        self.pages.append(page)

        page = FeedPage(self, FeedType.RSS, 'feeds/posts/default.rss', withsuffix=True)
        self.pages.append(page)

    def filterpages(self, pagespecs):
        recentlimit = None
        if self.opts.recent:
            try:
                val = parseinterval(self.opts.recent)
                recentlimit = int(time.time() - val)
            except:
                raise RuntimeException('--recent must be a time interval')
            
        if self.opts.buildall:
            if pagespecs:
                print('Ignoring pagespecs, building --all')
            if recentlimit is not None:
                print('Ignoring --recent, building --all')
            return list(self.pages)
        
        if not pagespecs and recentlimit is None:
            print('No pages requested')
            return []
        
        try:
            pagespecs = parsespecs(pagespecs)
        except ValueError as ex:
            raise RuntimeException(str(ex))
        
        if self.opts.buildonly:
            pagelist = [ page for page in self.pages if page.matchspecs(pagespecs, recentlimit) is not None ]
        else:
            for page in self.pages:
                if page.backdependpages:
                    for backdep, dep in page.backdependpages:
                        if backdep.dependpages is None:
                            backdep.dependpages = []
                        backdep.dependpages.append( (page, dep) )
            pagedeps = []
            for page in self.pages:
                dep = page.matchspecs(pagespecs, recentlimit)
                if dep is not None:
                    pagedeps.append( (page, dep) )
            pageset = PageSet()
            for page, dep in pagedeps:
                pageset.add(page)
            for page, dep in pagedeps:
                if page.dependpages:
                    for page2, dep2 in page.dependpages:
                        if dep & dep2:
                            pageset.add(page2)
            pagelist = list(pageset)
            
        if not pagelist:
            showls = [ spec for spec, dep in pagespecs ]
            if recentlimit is not None:
                showls.append('(recent %s)' % (self.opts.recent,))
            val = ', '.join(showls)
            raise RuntimeException('No pages match ' + val)
        return pagelist

    def build(self, pagelist):
        print('Building %s...' % (xofypages(len(pagelist), len(self.pages)),))
        if len(pagelist) < 20 or self.opts.longlist:
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
            
            print('Committing %s...' % (xofypages(len(pagelist), len(self.pages)),))
            for page in pagelist:
                page.commit()

        for page in self.draftentries:
            print('Draft: %s%s' % (self.serverurl, page.outuri,))
