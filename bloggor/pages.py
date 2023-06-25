import os.path
import datetime
import feedgenerator

class Page:
    def __init__(self, ctx):
        self.ctx = ctx
        self.opts = ctx.opts
        self.jenv = ctx.jenv
        self.mdenv = ctx.mdenv

        self.outpath = None
        self.tempoutpath = None
        self.outuri = None
        self.outdir = None

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

    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.outuri)

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

        
class StaticMDPage(Page):
    def __init__(self, ctx, filename, outpath):
        Page.__init__(self, ctx)
        self.dirpath = os.path.join(ctx.opts.srcdir, 'pages')
        self.filename = filename
        self.outpath = outpath

        self.path = os.path.join(self.dirpath, self.filename)

        self.complete()

    def read(self):
        fl = open(self.path)
        dat = fl.read()
        fl.close()
        self.mdenv.reset()
        self.body = self.mdenv.convert(dat)
        self.metadata = self.mdenv.Meta

        self.title = None
        ls = self.metadata.get('title', None)
        if ls:
            self.title = ' '.join(ls)

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
        self.outpath = 'recent.html'
        self.complete()

    def build(self):
        # 20 recent entries, plus enough to round out the first month
        pos = len(self.ctx.entries) - 20
        if pos < 0:
            pos = 0
        else:
            while pos > 0 and self.ctx.entries[pos-1].shortmonth == self.ctx.entries[pos].shortmonth:
                pos -= 1
        entries = self.ctx.entries[ pos : ]
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
    def __init__(self, ctx, year):
        Page.__init__(self, ctx)
        self.year = year
        self.outpath = '%d/index.html' % (self.year,)
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
    def __init__(self, ctx, tag):
        Page.__init__(self, ctx)
        self.tag = tag
        self.outpath = os.path.join('tag', tagfilename(tag)+'.html')
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
        self.complete()

        self.feed_url = self.opts.serverurl+outpath
        if not withsuffix:
            self.feed_url, _, _ = self.feed_url.rpartition('.')

    def __repr__(self):
        return '<%s (%s) "%s">' % (self.__class__.__name__, self.format, self.outuri)

    def build(self):
        if self.format == constants.ATOM:
            cla = feedgenerator.Atom1Feed
        elif self.format == constants.RSS:
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

        entries = self.ctx.entries[ -25 : ]
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
            self.type = constants.HTML
            outfile = filename
        elif filename.endswith('.md'):
            self.type = constants.MD
            outfile = filename[ : -3 ] + '.html'
        else:
            raise RuntimeException(self.path+': Unrecognized entry format: ' + filename)

        self.outpath = os.path.relpath(os.path.join(self.dirpath, outfile), start=ctx.entriesdir)
        if self.outpath.startswith('..') or self.outpath.startswith('/'):
            raise RuntimeException(self.path+': Bad outpath: ' + self.outpath)

        self.title = None
        self.tags = None
        self.index = None
        self.commentthread = None
        self.comments = None
        self.complete()

    def read(self):
        if self.type == constants.HTML:
            mfl = MetaFile(self.path)
            body, metadata = mfl.read()
        elif self.type == constants.MD:
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

        ls = metadata.get('published')
        if not ls:
            raise RuntimeException(self.path+': No published date')
        val = ''.join(ls)
        try:
            self.publishedraw = parsedate(val)
            self.published = datetime.datetime.fromisoformat(self.publishedraw)
        except ValueError:
            raise RuntimeException(self.path+': Invalid published date: '+val)

        self.updatedraw = None
        self.updated = None
        ls = metadata.get('updated')
        if ls:
            val = ''.join(ls)
            try:
                self.updatedraw = parsedate(val)
                self.updated = datetime.datetime.fromisoformat(self.updatedraw)
            except ValueError:
                raise RuntimeException(self.path+': Invalid updated date: '+val)
        if self.updated is None or self.updated < self.published:
            self.updatedraw = self.publishedraw
            self.updated = self.published

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
        
        self.draft = False  ###
        ### What is the following for drafts? Current date? End of the given month?

        publocal = self.published.astimezone(constants.eastern_tz)
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
        if self.index > 0:
            preventry = self.ctx.entries[self.index-1]
        if self.index < len(self.ctx.entries)-1:
            nextentry = self.ctx.entries[self.index+1]

        fl = self.openwrite()
        template = self.jenv.get_template('entry.html')
        fl.write(template.render(
            entry=self,
            title=self.title,
            nextentry=nextentry,
            preventry=preventry))
        fl.close()


from bloggor import constants
from bloggor.excepts import RuntimeException
from bloggor.metafile import MetaFile
from bloggor.util import tagfilename, parsedate, relativetime, excerpthtml, sortform
