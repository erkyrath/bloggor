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
        entries = self.ctx.entries[ -20 : ]
        ### back up to a month break?
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
        self.outpath = 'year-%d.html' % (self.year,)
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
        
    
class TagListPage(Page):
    def __init__(self, ctx):
        Page.__init__(self, ctx)
        self.outpath = 'tags.html'
        self.complete()

    def build(self):
        tags = [ (tag, len(ls)) for tag, ls in self.ctx.entriesbytag.items() ]
        tags.sort()
        
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
        tags = [ (tag, len(ls)) for tag, ls in self.ctx.entriesbytag.items() ]
        tags.sort(key=lambda tup:(-tup[1], tup[0]))
        
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
    def __init__(self, ctx, format, outpath):
        Page.__init__(self, ctx)
        self.outpath = outpath
        self.format = format
        self.complete()

    def build(self):
        if self.format == constants.ATOM:
            cla = feedgenerator.Atom1Feed
        elif self.format == constants.RSS:
            cla = feedgenerator.Rss201rev2Feed
        else:
            raise RuntimeException('unknown feed format: '+self.format)
        
        feed = cla(
            title = 'Zarf Updates',
            link = self.opts.serverurl,
            author_name = 'Andrew Plotkin',
            description = 'Interactive fiction, narrative in games, and so on',
            language = 'en',
            categories = ['foo', 'bar'], ###
        )

        entries = self.ctx.entries[ -25 : ]
        entries.reverse()

        for entry in entries:
            feed.add_item(
                title = entry.title,
                description = entry.body,
                link = self.opts.serverurl+entry.outuri,
                author_name = 'Andrew Plotkin',
                categories = entry.tags,
                pubdate = datetime.datetime.fromisoformat(entry.published),
                ### updateddate?
            )
        
        fl = self.openwrite()
        feed.write(fl, 'utf-8')
        fl.close()


HTML = 'html'
MD = 'md'
EST_TZ = datetime.timezone(datetime.timedelta(hours=-5))
        
class EntryPage(Page):
    def __init__(self, ctx, dirpath, filename):
        Page.__init__(self, ctx)
        self.dirpath = dirpath
        self.filename = filename

        self.path = os.path.join(self.dirpath, self.filename)
        
        if filename.endswith('.html'):
            self.type = HTML
            outfile = filename
        elif filename.endswith('.md'):
            self.type = MD
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
        if self.type == HTML:
            mfl = MetaFile(self.path)
            body, metadata = mfl.read()
        else:
            fl = open(self.path)
            dat = fl.read()
            fl.close()
            self.mdenv.reset()
            body = self.mdenv.convert(dat)
            metadata = self.mdenv.Meta

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
            self.published = parsedate(val)
        except ValueError:
            raise RuntimeException(self.path+': Invalid published date: '+val)

        self.updated = None
        ls = metadata.get('updated')
        if ls:
            val = ''.join(ls)
            try:
                self.updated = parsedate(val)
            except ValueError:
                raise RuntimeException(self.path+': Invalid updated date: '+val)
        if self.updated is None or self.updated < self.published:
            self.updated = self.published

        self.tags = []
        ls = metadata.get('tags', None)
        if ls:
            for val in ls:
                for tag in val.split(','):
                    tag = tag.strip().lower()
                    if tag:
                        self.tags.append(tag)

        self.bakedcomments = 0
        ls = metadata.get('bakedcomments', None)
        if ls:
            self.bakedcomments = int(ls[0])

        if not self.title:
            raise RuntimeException(self.path+': No title')

        # self.index is set after all posts are read and sorted
        # same goes for self.comments
        
        self.draft = False  ###
        ### What is the following for drafts? Current date? End of the given month?

        pubtup = datetime.datetime.fromisoformat(self.published)
        pubtuplocal = pubtup.astimezone(EST_TZ)
        self.longpublished = pubtuplocal.strftime('%A, %B %d, %Y').replace(' 0', ' ')
        self.year = pubtuplocal.year
        self.monthname = pubtuplocal.strftime('%B %Y')
        self.shortdate = pubtuplocal.strftime('%Y-%m-%d')

        updatup = datetime.datetime.fromisoformat(self.updated)
        if updatup - pubtup < datetime.timedelta(minutes=15):
            self.longupdated = None
        else:
            self.longupdated = relativetime(updatup, pubtup)

        # shortdate doesn't always match outdir, so we don't check that.

        
    def build(self):
        preventry = None
        nextentry = None
        if self.index > 0:
            preventry = self.ctx.entries[self.index-1]
        if self.index < len(self.ctx.entries)-1:
            nextentry = self.ctx.entries[self.index+1]

        if not self.comments:
            totalcomments = self.bakedcomments
        else:
            totalcomments = self.bakedcomments + len(self.comments)
            
        fl = self.openwrite()
        template = self.jenv.get_template('entry.html')
        fl.write(template.render(
            entry=self,
            title=self.title,
            comments=self.comments,
            totalcomments=totalcomments,
            nextentry=nextentry,
            preventry=preventry))
        fl.close()


from bloggor import constants
from bloggor.excepts import RuntimeException
from bloggor.metafile import MetaFile
from bloggor.util import tagfilename, parsedate, relativetime, excerpthtml
