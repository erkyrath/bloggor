import os.path
import datetime
import feedgenerator
from fnmatch import fnmatch

class Page:
    def __init__(self, ctx):
        self.ctx = ctx
        self.opts = ctx.opts
        self.jenv = ctx.jenv
        self.mdenv = ctx.mdenv

        self.path = None
        self.inpath = None
        self.inuri = None
        self.outpath = None
        self.tempoutpath = None
        self.outuri = None
        self.outdir = None
        self.frequent = False

        self.backdependpages = None
        self.dependpages = None

    def complete(self):
        self.outuri, dot, suffix = self.outpath.rpartition('.')
        if suffix not in ('html', 'rss', 'xml'):
            raise RuntimeException(self.outpath+': not html or other known suffix')
        if '.' in self.outuri:
            raise RuntimeException(self.outuri+': uri contains dot')
            
        self.outdir = os.path.dirname(self.outpath)
        if not self.opts.notemp:
            self.tempoutpath = self.outpath + '_tmp.' + suffix
        else:
            self.tempoutpath = self.outpath

        if self.path is not None:
            self.inpath = os.path.relpath(self.path, start=self.opts.srcdir)
            self.inuri, dot, _ = self.inpath.rpartition('.')

    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.outuri)

    def matchspecs(self, specs):
        res = None
        
        for (spec, dep) in specs:
            if self.match(spec):
                if res is None:
                    res = dep
                else:
                    res |= dep
                if res == Depend.ALL:
                    return Depend.ALL

        return res

    def match(self, spec):
        if '*' in spec:
            if fnmatch(self.outuri, spec):
                return True
        else:
            if self.outpath == spec:
                return True
            if self.outuri == spec:
                return True
            if '.' in spec:
                if self.inpath is not None and self.inpath.endswith(spec):
                    return True
        return False

    def openwrite(self):
        if self.outdir:
            os.makedirs(os.path.join(self.opts.destdir, self.outdir), exist_ok=True)
            
        fl = open(os.path.join(self.opts.destdir, self.tempoutpath), 'w')
        return fl

    def commit(self):
        assert self.tempoutpath != self.outpath
        os.replace(os.path.join(self.opts.destdir, self.tempoutpath), os.path.join(self.opts.destdir, self.outpath))

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

    def read(self):
        pass
        
    def build(self):
        fl = self.openwrite()
        template = self.jenv.get_template(self.template)
        fl.write(template.render())
        fl.close()

        
class StaticPage(Page):
    def __init__(self, ctx, dirpath, filename):
        Page.__init__(self, ctx)
        self.dirpath = dirpath
        self.filename = filename

        self.path = os.path.join(self.dirpath, self.filename)
        
        if filename.endswith('.html'):
            self.type = FileType.HTML
            outfile = filename
        elif filename.endswith('.md'):
            self.type = FileType.MD
            outfile = filename[ : -3 ] + '.html'
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + filename)

        self.outpath = os.path.relpath(os.path.join(self.dirpath, outfile), start=ctx.pagesdir)
        if self.outpath.startswith('..') or self.outpath.startswith('/'):
            raise RuntimeException(self.path+': Bad outpath: ' + self.outpath)
        self.complete()

    def read(self):
        if self.type == FileType.HTML:
            mfl = MetaFile(self.path)
            body, metadata = mfl.read()
        elif self.type == FileType.MD:
            fl = open(self.path)
            dat = fl.read()
            fl.close()
            self.mdenv.reset()
            body = self.mdenv.convert(dat)
            metadata = self.mdenv.Meta
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + self.type)

        self.body = body
        self.metadata = metadata

        self.title = None
        ls = self.metadata.get('title', None)
        if ls:
            self.title = ' '.join(ls)

        if not self.title:
            raise RuntimeException(self.path+': No title')

    def build(self):
        fl = self.openwrite()
        template = self.jenv.get_template('static.html')
        fl.write(template.render(
            title=self.title,
            body=self.body))
        fl.close()

        
class FrontPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'index.html'
        self.frequent = True
        self.backdependpages = [ (page, Depend.ALL) for page in ctx.recententries ]
        self.complete()

    def build(self):
        fl = self.openwrite()
        template = self.jenv.get_template('front.html')
        fl.write(template.render(
            title=None,
            entries=self.ctx.recententries,
            recentfew=self.ctx.recentfew))
        fl.close()


class RecentEntriesPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)

        # 20 recent entries, plus enough to round out the first month
        pos = len(self.ctx.liveentries) - 20
        if pos < 0:
            pos = 0
        else:
            while pos > 0 and self.ctx.liveentries[pos-1].shortmonth == self.ctx.liveentries[pos].shortmonth:
                pos -= 1
        self.livepos = pos
        
        self.outpath = 'recent.html'
        self.frequent = True
        entries = self.ctx.liveentries[ self.livepos : ]
        self.backdependpages = [ (page, Depend.ALLBUTBODY) for page in entries ]
        self.complete()

    def build(self):
        entries = self.ctx.liveentries[ self.livepos : ]
        entries.reverse()
        
        yearls = list(self.ctx.entriesbyyear.keys())
        yearls.sort(reverse=True)

        fl = self.openwrite()
        template = self.jenv.get_template('recent.html')
        fl.write(template.render(
            title='Recent Posts',
            entries=entries,
            years=yearls,
            recentfew=self.ctx.recentfew))
        fl.close()
        
    
class YearEntriesPage(Page):
    def __init__(self, ctx, year, pagels):
        Page.__init__(self, ctx)
        self.year = year
        self.outpath = '%d/index.html' % (self.year,)
        self.backdependpages = [ (page, Depend.ALLBUTBODY) for page in pagels ]
        self.complete()

    def build(self):
        entries = self.ctx.entriesbyyear[self.year]

        yearls = list(self.ctx.entriesbyyear.keys())
        yearls.sort(reverse=True)

        fl = self.openwrite()
        template = self.jenv.get_template('recent.html')
        fl.write(template.render(
            title='Posts From %d' % (self.year,),
            year=self.year,
            entries=entries,
            years=yearls))
        fl.close()
        
    
class HistoryPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'history.html'
        self.frequent = True
        self.backdependpages = [ (page, Depend.CREATED|Depend.PUBDATE) for page in ctx.liveentries ]
        self.complete()

    def build(self):
        yearls = list(self.ctx.entriesbyyear.keys())
        yearls.sort()

        monthls = [
            ('January', '01'), ('February', '02'), ('March', '03'),
            ('April', '04'), ('May', '05'), ('June', '06'),
            ('July', '07'), ('August', '08'), ('September', '09'),
            ('October', '10'), ('November', '11'), ('December', '12'),
        ]

        fl = self.openwrite()
        template = self.jenv.get_template('history.html')
        fl.write(template.render(
            title='Blog Archive',
            years=yearls,
            months=monthls,
            recentfew=self.ctx.recentfew))
        fl.close()


class TagListPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'tags.html'
        self.frequent = True
        self.backdependpages = [ (page, Depend.TAGS|Depend.CREATED) for page in ctx.liveentries ]
        self.complete()

    def build(self):
        tags = [ (tag, sortform(tag), len(ls)) for tag, ls in self.ctx.entriesbytag.items() ]
        tags.sort(key=lambda tup:tup[1])
        
        fl = self.openwrite()
        template = self.jenv.get_template('tags.html')
        fl.write(template.render(
            title='All Tags (Alphabetical)',
            tags=tags,
            sortby='alpha',
            recentfew=self.ctx.recentfew))
        fl.close()


class TagListFreqPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'tags-freq.html'
        self.frequent = True
        self.backdependpages = [ (page, Depend.TAGS|Depend.CREATED) for page in ctx.liveentries ]
        self.complete()

    def build(self):
        tags = [ (tag, sortform(tag), len(ls)) for tag, ls in self.ctx.entriesbytag.items() ]
        tags.sort(key=lambda tup:(-tup[2], tup[1]))
        
        fl = self.openwrite()
        template = self.jenv.get_template('tags.html')
        fl.write(template.render(
            title='All Tags (by Frequency)',
            tags=tags,
            sortby='freq',
            recentfew=self.ctx.recentfew))
        fl.close()


class TagPage(Page):
    def __init__(self, ctx, tag, pagels):
        Page.__init__(self, ctx)
        self.tag = tag
        self.outpath = os.path.join('tag', tagfilename(tag)+'.html')
        self.backdependpages = [ (page, Depend.TAGS|Depend.PUBDATE|Depend.TITLE) for page in pagels ]
        self.complete()

    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.tag)

    def build(self):
        entries = self.ctx.entriesbytag[self.tag]
        entries.reverse()
        oneentry = (len(entries) == 1)
        
        fl = self.openwrite()
        template = self.jenv.get_template('tag.html')
        fl.write(template.render(
            title='Tag: '+self.tag,
            tag=self.tag,
            entries=entries,
            oneentry=oneentry))
        fl.close()

class FeedPage(Page):
    def __init__(self, ctx, format, outpath, withsuffix=False):
        Page.__init__(self, ctx)
        self.outpath = outpath
        self.format = format
        entries = self.ctx.liveentries[ -25 : ]
        self.backdependpages = [ (page, Depend.ALL) for page in entries ]
        self.complete()

        self.feed_url = self.opts.serverurl+outpath
        if not withsuffix:
            self.feed_url, _, _ = self.feed_url.rpartition('.')

    def __repr__(self):
        return '<%s (%s) "%s">' % (self.__class__.__name__, self.format, self.outuri)

    def build(self):
        if self.format == FeedType.ATOM:
            cla = feedgenerator.Atom1Feed
        elif self.format == FeedType.RSS:
            cla = feedgenerator.Rss201rev2Feed
        else:
            raise RuntimeException('unknown feed format: '+self.format)

        commontags = [ tag for tag, ls in self.ctx.entriesbytag.items() if len(ls) > 1 ]
        commontags.sort()
        
        feed = cla(
            title = 'Zarf Updates',
            link = self.opts.serverurl,
            author_name = 'Andrew Plotkin',
            description = 'Interactive fiction, narrative in games, and so on',
            feed_url = self.feed_url,
            language = 'en',
            categories = commontags,
        )

        entries = self.ctx.liveentries[ -25 : ]
        entries.reverse()

        for entry in entries:
            feed.add_item(
                title = entry.title,
                description = entry.excerpt,
                content = entry.body,
                link = self.opts.serverurl+entry.outuri,
                author_name = 'Andrew Plotkin',
                categories = entry.tags,
                pubdate = entry.published,
                updateddate = entry.updated,
            )
        
        fl = self.openwrite()
        feed.write(fl, 'utf-8')
        fl.close()

        
class EntryPage(Page):
    def __init__(self, ctx, dirpath, filename):
        Page.__init__(self, ctx)
        self.dirpath = dirpath
        self.filename = filename

        self.path = os.path.join(self.dirpath, self.filename)
        
        if filename.endswith('.html'):
            self.type = FileType.HTML
            outfile = filename
        elif filename.endswith('.md'):
            self.type = FileType.MD
            outfile = filename[ : -3 ] + '.html'
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + filename)

        self.outpath = os.path.relpath(os.path.join(self.dirpath, outfile), start=ctx.entriesdir)
        if self.outpath.startswith('..') or self.outpath.startswith('/'):
            raise RuntimeException(self.path+': Bad outpath: ' + self.outpath)

        self.live = False
        self.title = None
        self.tags = None
        self.index = None
        self.commentthread = None
        self.comments = None
        self.fedipostid = None
        
        self.publishedraw = None
        self.published = None
        self.updatedraw = None
        self.updated = None

        self.complete()

    def __repr__(self):
        val = '' if self.live else ' DRAFT'
        return '<%s%s "%s">' % (self.__class__.__name__, val, self.outuri)

    def read(self):
        if self.type == FileType.HTML:
            mfl = MetaFile(self.path)
            body, metadata = mfl.read()
        elif self.type == FileType.MD:
            fl = open(self.path)
            dat = fl.read()
            fl.close()
            self.mdenv.reset()
            body = self.mdenv.convert(dat)
            metadata = self.mdenv.Meta
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + self.type)

        self.body = body
        self.metadata = metadata

        self.excerpt = excerpthtml(body)

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

        # self.index is set after all posts are read and sorted
        # same goes for self.comments

        try:
            self.fedipostid = ls_as_value(metadata.get('fedipostid'))
        except ValueError as ex:
            raise RuntimeException(self.path+': Fedipostid not valid: '+str(ex))
        
        try:
            self.live = ls_as_bool(metadata.get('live'))
        except ValueError as ex:
            raise RuntimeException(self.path+': Live not valid: '+str(ex))

        if not self.live:
            self.longpublished = 'DRAFT'
            self.longupdated = None
            return

        try:
            val = ls_as_value(metadata.get('published'))
        except ValueError as ex:
            raise RuntimeException(self.path+': Invalid published date: '+str(ex))
        if val is None:
            raise RuntimeException(self.path+': No published date')
        try:
            self.publishedraw = parsedate(val)
            self.published = datetime.datetime.fromisoformat(self.publishedraw)
        except ValueError:
            raise RuntimeException(self.path+': Invalid published date: '+val)

        try:
            val = ls_as_value(metadata.get('updated'))
        except ValueError as ex:
            raise RuntimeException(self.path+': Invalid updated date: '+str(ex))
        if val is not None:
            try:
                self.updatedraw = parsedate(val)
                self.updated = datetime.datetime.fromisoformat(self.updatedraw)
            except ValueError:
                raise RuntimeException(self.path+': Invalid updated date: '+val)
        if self.updated is None or self.updated < self.published:
            self.updatedraw = self.publishedraw
            self.updated = self.published

        publocal = self.published.astimezone(eastern_tz)
        self.longpublished = publocal.strftime('%A, %B %d, %Y').replace(' 0', ' ')
        self.year = publocal.year
        self.month = publocal.month
        self.monthname = publocal.strftime('%B %Y')
        self.shortdate = publocal.strftime('%Y-%m-%d')
        self.shortmonth = publocal.strftime('%Y-%m')

        if self.updated - self.published < datetime.timedelta(minutes=15):
            self.longupdated = None
        else:
            self.longupdated = relativetime(self.updated, self.published)

        # shortdate doesn't always match outdir, so we don't check that.

        
    def build(self):
        preventry = None
        nextentry = None
        if self.live and self.index > 0:
            preventry = self.ctx.liveentries[self.index-1]
        if self.live and self.index < len(self.ctx.liveentries)-1:
            nextentry = self.ctx.liveentries[self.index+1]

        fl = self.openwrite()
        template = self.jenv.get_template('entry.html')
        fl.write(template.render(
            entry=self,
            title=self.title,
            nextentry=nextentry,
            preventry=preventry))
        fl.close()


from bloggor.constants import FileType, FeedType, Depend
from bloggor.constants import eastern_tz
from bloggor.excepts import RuntimeException
from bloggor.metafile import MetaFile, ls_as_bool, ls_as_value
from bloggor.util import tagfilename, parsedate, relativetime, excerpthtml, sortform
