#!/usr/bin/env python3

import sys
import os
import re
import datetime
import optparse
import json
import xml.sax
from xml.sax.handler import ContentHandler

from readtable import read_table

popt = optparse.OptionParser()

popt.add_option('-o', '--out',
                action='store', dest='outdir',
                help='directory to write posts')

(opts, args) = popt.parse_args()

if args:
    print('usage: parse.py [ -o outdir ]')
    sys.exit()

feedatom = 'Takeout/Blogger/Blogs/Zarf Updates/feed.atom'

EST_TZ = datetime.timezone(datetime.timedelta(hours=-5))

pat_divpara = re.compile('^<div class="para"(?: style="margin-[a-z]+: 1em; margin-[a-z]+: 1em;")?>(.*)</div>$')
pat_divparastart = re.compile('^<div class="para"(?: style="margin-[a-z]+: 1em; margin-[a-z]+: 1em;")?>$')
pat_gameshelf = re.compile('["\'](http[s]?://[a-z0-9_.]*jmac.org/[^"\']*)["\']', flags=re.IGNORECASE)
pat_blogspot = re.compile('["\'](http[s]?://[a-z0-9_.]*(?:googleusercontent|blogspot).com/[^"\']*)["\']', flags=re.IGNORECASE)
pat_blogzarf = re.compile('["\'](http[s]?://blog.zarfhome.com/[^"\']*)["\']', flags=re.IGNORECASE)

pat_morebreak = re.compile('<!--more-->', flags=re.IGNORECASE)
pat_fatbullet = re.compile('<li>\n*<br/?>', flags=re.IGNORECASE+re.MULTILINE)

pat_bakedline = re.compile('<hr */?>\n*<h3>\n*Comments imported from Gameshelf</h3>\n*', flags=re.MULTILINE)
pat_bakedhead = re.compile('<hr */?>\n*<b>([^<]+)</b> [(]([^)]+)[)]:<br */>', flags=re.MULTILINE)

class Entry:
    def __init__(self, map):
        assert (map['status'] == 'LIVE')
        assert (map['author/name'] == 'Andrew Plotkin')
        self.id = map['id']
        self.title = map['title']
        self.filename = map['filename']
        self.content = map['content']
        self.createdraw = map['created']
        self.publishedraw = map['published']
        self.updatedraw = map['updated']
        self.tags = []
        if 'tags' in map:
            self.tags.extend(map['tags'])

        self.comments = []
        self.replies = []
        self.flatreplies = []

        (_, _, val) = self.id.rpartition('-')
        self.shortid = val

        self.content = self.modernize(self.content)
        self.content = self.addmore(self.content)
        self.content = self.degameshelf(self.content)
        self.content = self.deblogger(self.content)
        self.content, self.bakedcomments = self.trimbaked(self.content)

    def __repr__(self):
        return '<Entry "%s">' % (self.filename,)

    def modernize(self, text):
        text = pat_fatbullet.sub('<li>', text)
            
        ls = []
        for ln in text.split('\n'):
            match = pat_divpara.match(ln)
            if match:
                ln = '<p>%s</p>' % (match.group(1),)
            if ls and pat_divparastart.match(ls[-1]) and ln.endswith('</div>'):
                ln = ln[ : -6 ]
                ln = '<p>%s</p>' % (ln,)
                del ls[-1]
            ls.append(ln)
            
        ls2 = []
        for ln in ls:
            ln = ln.replace('</div>', '</div>\n')
            if ln.endswith('\n'):
                ln = ln[ : -1 ]
            ls2.append(ln)
            
        return '\n'.join(ls2)

    def addmore(self, text):
        match = pat_morebreak.search(text)
        if match:
            pos = match.end()
            text = text[ : pos ] + '\n<a name="more"></a>\n' + text[ pos : ]
        return text
        
    def degameshelf(self, text):
        def func(match):
            url = match.group(1)
            if url in gameshelf_image_table:
                newurl, prefix, hostpost = gameshelf_image_table[url]
                #return '"$$GSHELFIMAGE:%s:%s$$"' % (prefix, newurl,)
                return '"/pic/%s/%s"' % (prefix, newurl,)
            if url in gameshelf_post_table:
                shortid, newurl = gameshelf_post_table[url]
                #return '"$$GSHELFPOST:%s:%s$$"' % (shortid, newurl,)
                return '"%s"' % (newurl[ : -5 ],)
            return '"%s"' % (url,)
        text = pat_gameshelf.sub(func, text)
        return text

    def deblogger(self, text):
        def func(match):
            url = match.group(1)
            if url in blogger_image_table:
                newurl, size, prefix, hostpost = blogger_image_table[url]
                #return '"$$BSPOTIMAGE:%s:%s$$"' % (prefix, newurl,)
                return '"/pic/%s/%s"' % (prefix, newurl,)
            return '"%s"' % (url,)
        text = pat_blogspot.sub(func, text)
        def func2(match):
            url = match.group(1)
            if url in blogger_post_table:
                shortid, newurl = blogger_post_table[url]
                #return '"$$BZARFPOST:%s:%s$$"' % (shortid, newurl,)
                return '"%s"' % (newurl[ : -5 ],)
            return '"%s"' % (url,)
        text = pat_blogzarf.sub(func2, text)
        return text

    def trimbaked(self, text):
        match = pat_bakedline.search(text)
        if not match:
            return text, []
        comthread = text[ match.end() : ]
        text = text[ : match.start() ]
        comments = []

        ls = list(pat_bakedhead.finditer(comthread))
        assert ls[0].start() == 0
        for ix, match in enumerate(ls):
            authorname = match.group(1)
            pubdate = datetime.datetime.strptime(match.group(2), '%b %d, %Y at %I:%M %p')
            pubdate = pubdate.replace(tzinfo=EST_TZ).astimezone(datetime.timezone.utc)
            if ix+1 < len(ls):
                endpos = ls[ix+1].start()
            else:
                endpos = len(comthread)
            seg = comthread[match.end() : endpos]
            seg = seg.strip()
            comments.append(BakedComment(authorname, pubdate, seg))
            
        return text, comments

    def jsonmap(self):
        map = {}
        map['id'] = self.id
        map['shortid'] = self.shortid
        map['title'] = self.title
        map['filename'] = self.filename
        map['createdraw'] = self.createdraw
        map['publishedraw'] = self.publishedraw
        map['updatedraw'] = self.updatedraw
        map['tags'] = self.tags
        return map


class Comment:
    def __init__(self, map):
        assert (map['status'] == 'LIVE')
        self.id = map['id']
        self.parentid = map['parent']
        self.inreplyto = map.get('inreplyto', None) or None
        self.authorname = map.get('author/name', None) or None
        self.authoruri = map.get('author/uri', None) or None
        self.authortype = map['author/type']
        self.content = map['content']
        self.createdraw = map['created']
        self.publishedraw = map['published']
        self.updatedraw = map['updated']

        self.depth = None
        self.replies = []

        (_, _, val) = self.id.rpartition('-')
        self.shortid = val
        
    def __repr__(self):
        return '<Comment %s (%s)>' % (self.shortid, self.depth,)

    def jsonmap(self):
        map = {}
        map['id'] = self.id
        map['shortid'] = self.shortid
        map['parentid'] = self.parentid
        map['inreplyto'] = self.inreplyto
        map['authorname'] = self.authorname
        map['authoruri'] = self.authoruri
        map['authortype'] = self.authortype
        map['createdraw'] = self.createdraw
        map['publishedraw'] = self.publishedraw
        map['updatedraw'] = self.updatedraw
        return map

class BakedComment:
    def __init__(self, authorname, pubdate, content):
        self.authorname = authorname
        self.publishedraw = pubdate.isoformat()
        self.content = content

pat_dashes = re.compile(r'^(---+)\s*$')

def writeescapedashes(fl, text, delim=3):
    ls = text.split('\n')
    for ln in ls:
        match = pat_dashes.match(ln)
        if match and len(match.group(1)) == delim:
            ln = '-' + ln
        fl.write(ln+'\n')
    
class Handler(ContentHandler):
    depth = None
    tagnesting = []

    characcum = None

    blogtitle = None
    entries = []
    comments = []

    curfields = None

    def startDocument(self):
        self.depth = 0
        
    def startElement(self, name, attrs):
        #print('Start element:', self.depth, name, dict(attrs))
        elhan = getattr(self, 'starttag_%s_%d' % (name.replace(':', '_'), self.depth,), None)
        if elhan:
            elhan(attrs)
        self.tagnesting.append(name)
        self.depth += 1
        
    def endElement(self, name):
        self.depth -= 1
        assert (name == self.tagnesting[-1])
        del self.tagnesting[-1]
        #print('End element:', self.depth, name)
        elhan = getattr(self, 'endtag_%s_%d' % (name.replace(':', '_'), self.depth,), None)
        if elhan:
            elhan()

    def characters(self, val):
        if self.characcum is not None:
            self.characcum.append(val)

            
    def startaccum(self):
        if self.characcum is not None:
            raise Exception('re-entrant startaccum')
        self.characcum = []

    def endaccum(self):
        if self.characcum is None:
            raise Exception('unstarted endaccum')
        val = ''.join(self.characcum)
        self.characcum = None
        return val

    
    def starttag_title_1(self, attrs):
        self.startaccum()
    def endtag_title_1(self):
        self.blogtitle = self.endaccum()

    def starttag_entry_1(self, attrs):
        self.curfields = {}
    def endtag_entry_1(self):
        map = self.curfields
        self.curfields = None
        maptype = map.get('type')
        if maptype == 'POST':
            entry = Entry(map)
            self.entries.append(entry)
        elif maptype == 'COMMENT':
            if 'SPAM' in map['status']:
                return
            if 'GHOSTED' in map['status']:
                return
            comment = Comment(map)
            self.comments.append(comment)

    def starttag_content_2(self, attrs):
        assert (attrs.get('type') == 'html')
        self.startaccum()
    def endtag_content_2(self):
        self.curfields['content'] = self.endaccum()
        
    def starttag_id_2(self, attrs):
        self.startaccum()
    def endtag_id_2(self):
        self.curfields['id'] = self.endaccum()
        
    def starttag_title_2(self, attrs):
        self.startaccum()
    def endtag_title_2(self):
        self.curfields['title'] = self.endaccum()
        
    def starttag_blogger_type_2(self, attrs):
        self.startaccum()
    def endtag_blogger_type_2(self):
        self.curfields['type'] = self.endaccum()
        
    def starttag_blogger_status_2(self, attrs):
        self.startaccum()
    def endtag_blogger_status_2(self):
        self.curfields['status'] = self.endaccum()
        
    def starttag_blogger_filename_2(self, attrs):
        self.startaccum()
    def endtag_blogger_filename_2(self):
        self.curfields['filename'] = self.endaccum()
        
    def starttag_blogger_parent_2(self, attrs):
        self.startaccum()
    def endtag_blogger_parent_2(self):
        self.curfields['parent'] = self.endaccum()
        
    def starttag_blogger_inReplyTo_2(self, attrs):
        self.startaccum()
    def endtag_blogger_inReplyTo_2(self):
        val = self.endaccum()
        if val:
            self.curfields['inreplyto'] = val
        
    def starttag_category_2(self, attrs):
        val = attrs.get('term')
        if not val:
            return
        if 'tags' in self.curfields:
            self.curfields['tags'].append(val)
        else:
            self.curfields['tags'] = [ val ]
        
    def starttag_blogger_created_2(self, attrs):
        self.startaccum()
    def endtag_blogger_created_2(self):
        self.curfields['created'] = self.endaccum()
        
    def starttag_published_2(self, attrs):
        self.startaccum()
    def endtag_published_2(self):
        self.curfields['published'] = self.endaccum()
        
    def starttag_updated_2(self, attrs):
        self.startaccum()
    def endtag_updated_2(self):
        self.curfields['updated'] = self.endaccum()
        
    def starttag_name_3(self, attrs):
        if self.tagnesting[-1] == 'author':
            self.startaccum()
    def endtag_name_3(self):
        if self.tagnesting[-1] == 'author':
            self.curfields['author/name'] = self.endaccum()
        
    def starttag_uri_3(self, attrs):
        if self.tagnesting[-1] == 'author':
            self.startaccum()
    def endtag_uri_3(self):
        if self.tagnesting[-1] == 'author':
            self.curfields['author/uri'] = self.endaccum()
        
    def starttag_blogger_type_3(self, attrs):
        if self.tagnesting[-1] == 'author':
            self.startaccum()
    def endtag_blogger_type_3(self):
        if self.tagnesting[-1] == 'author':
            self.curfields['author/type'] = self.endaccum()

# Go time

blogger_image_table = read_table('blogger-image-table', multi=True)
blogger_post_table = read_table('blogger-post-table', multi=True)
gameshelf_image_table = read_table('gameshelf-image-table', multi=True)
gameshelf_post_table = read_table('gameshelf-post-table', multi=True)
post_name_table = read_table('post-name-table', multi=True)

handler = Handler()

fl = open(feedatom, 'rb')
xml.sax.parse(fl, handler)
fl.close()

entries, comments = handler.entries, handler.comments

entriesmap = {}
for ent in entries:
    entriesmap[ent.id] = ent

entries.sort(key=lambda ent: ent.publishedraw)

def depthifycomments(ent):
    map = {}
    for com in ent.comments:
        map[com.id] = com
    for com in ent.comments:
        if not com.inreplyto or com.inreplyto not in map:
            ent.replies.append(com)
        else:
            parentcom = map[com.inreplyto]
            parentcom.replies.append(com)
    ent.replies.sort(key=lambda com:com.publishedraw)
    def func(ls, depth=0):
        ls.sort(key=lambda com: com.publishedraw)
        for com in ls:
            com.depth = depth
            ent.flatreplies.append(com)
            func(com.replies, depth+1)
    func(ent.replies, 0)
    assert len(ent.comments) == len(ent.flatreplies)

for com in comments:
    ent = entriesmap[com.parentid]
    ent.comments.append(com)
for ent in entries:
    depthifycomments(ent)

if opts.outdir:
    print('Writing to %s...' % (opts.outdir,))
    os.makedirs(opts.outdir+'/entries', exist_ok=True)
    
    entls = []
    for ent in entries:
        prefix, filename = post_name_table[ent.shortid]
        assert filename == ent.filename
        assert ent.filename.endswith('.html')
        assert ent.filename.startswith('/')
        newuri = os.path.join(opts.outdir, 'entries', ent.filename[1:])
        
        os.makedirs(os.path.dirname(newuri), exist_ok=True)
        
        entls.append(ent.jsonmap())
        
        #fl = open('%s/entries/%s.html' % (opts.outdir, ent.shortid,), 'w')
        fl = open(newuri, 'w')
        fl.write('---\n')
        fl.write('title: %s\n' % (ent.title,))
        if ent.tags:
            fl.write('tags: %s\n' % (', '.join(ent.tags),))
        fl.write('bloggerid: %s\n' % (ent.id,))
        fl.write('published: %s\n' % (ent.publishedraw,))
        if ent.updatedraw.startswith('2017-05-25') or ent.updatedraw < ent.publishedraw:
            pass
        else:
            fl.write('updated:   %s\n' % (ent.updatedraw,))
        fl.write('---\n')
        fl.write(ent.content)
        fl.close()

    comls = []
    for ent in entries:
        if not ent.flatreplies and not ent.bakedcomments:
            continue
        for com in ent.flatreplies:
            comls.append(com.jsonmap())
        prefix, filename = post_name_table[ent.shortid]
        comuri = os.path.join(opts.outdir, 'entries', ent.filename[1:-5]+'.comments')
        fl = open(comuri, 'w')
        
        for com in ent.bakedcomments:
            fl.write('---\n')
            fl.write('source: gameshelf\n')
            fl.write('published: %s\n' % (com.publishedraw,))
            fl.write('format: html\n')
            fl.write('authorname: %s\n' % (com.authorname,))
            fl.write('---\n')
            writeescapedashes(fl, com.content)
            fl.write('\n')
            
        for com in ent.flatreplies:
            fl.write('---\n')
            fl.write('source: blogger\n')
            fl.write('bloggerid: %s\n' % (com.id,))
            fl.write('published: %s\n' % (com.publishedraw,))
            fl.write('format: whtml\n')
            if com.depth:
                fl.write('depth: %d\n' % (com.depth,))
            if com.authorname:
                fl.write('authorname: %s\n' % (com.authorname,))
            if com.authoruri == 'http://zarfhome.com/' and com.authorname == 'Andrew Plotkin':
                fl.write('authoruri: https://mastodon.gamedev.place/@zarfeblong\n')
            elif com.authoruri:
                fl.write('authoruri: %s\n' % (com.authoruri,))
            fl.write('---\n')
            writeescapedashes(fl, com.content)
            fl.write('\n')
            
        fl.write('---\n')
        fl.close()

    map = { 'entries':entls, 'comments':comls }
    fl = open(opts.outdir+'/all.json', 'w')
    json.dump(map, fl, indent=2)
    fl.close()

