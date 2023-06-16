#!/usr/bin/env python3

import sys
import os
import re
import optparse
import json
import xml.sax
from xml.sax.handler import ContentHandler

popt = optparse.OptionParser()

popt.add_option('-o', '--out',
                action='store', dest='outdir',
                help='directory to write posts')

(opts, args) = popt.parse_args()

feedatom = 'Takeout/Blogger/Blogs/Zarf Updates/feed.atom'

pat_divpara = re.compile('^<div class="para"(?: style="margin-[a-z]+: 1em; margin-[a-z]+: 1em;")?>(.*)</div>$')
pat_divparastart = re.compile('^<div class="para"(?: style="margin-[a-z]+: 1em; margin-[a-z]+: 1em;")?>$')
pat_gameshelf = re.compile('["\'](http[s]?://[a-z0-9_.]*jmac.org/[^"\']*)["\']', flags=re.IGNORECASE)
pat_blogspot = re.compile('["\'](http[s]?://[a-z0-9_.]*(?:googleusercontent|blogspot).com/[^"\']*)["\']', flags=re.IGNORECASE)

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

        (_, _, val) = self.id.rpartition('-')
        self.shortid = val

        self.content = self.modernize(self.content)
        self.content = self.degameshelf(self.content)
        self.content = self.deblogger(self.content)

    def modernize(self, text):
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

    def degameshelf(self, text):
        def func(match):
            url = match.group(1)
            if url in gameshelf_image_table:
                newurl = gameshelf_image_table[url]
                return '"$$GSHELFIMAGE:%s$$"' % (newurl,)
            if url in gameshelf_post_table:
                shortid, newurl = gameshelf_post_table[url]
                return '"$$GSHELFPOST:%s:%s$$"' % (shortid, newurl,)
            return '"%s"' % (url,)
        text = pat_gameshelf.sub(func, text)
        return text

    def deblogger(self, text):
        def func(match):
            url = match.group(1)
            if url in blogger_image_table:
                newurl, size = blogger_image_table[url]
                return '"$$BSPOTIMAGE:%s$$"' % (newurl,)
            return '"%s"' % (url,)
        text = pat_blogspot.sub(func, text)
        return text

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

        (_, _, val) = self.id.rpartition('-')
        self.shortid = val
        
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

pat_indent = re.compile('^[ \t]+')
    
def read_table(filename, multi=False):
    map = {}
    key = None
    fl = open(filename)
    for ln in fl.readlines():
        match = pat_indent.match(ln)
        if not match:
            key = ln.strip()
        else:
            if not multi:
                if key in map:
                    raise Exception('duplicate key: ' + key)
                map[key] = ln.strip()
            else:
                if key not in map:
                    map[key] = [ ln.strip() ]
                else:
                    map[key].append(ln.strip())
    return map
    
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
gameshelf_image_table = read_table('gameshelf-image-table')
gameshelf_post_table = read_table('gameshelf-post-table', multi=True)

handler = Handler()

fl = open(feedatom, 'rb')
xml.sax.parse(fl, handler)
fl.close()

entries, comments = handler.entries, handler.comments

entriesmap = {}
for ent in entries:
    entriesmap[ent.id] = ent

entries.sort(key=lambda ent: ent.publishedraw)

def commentsortkey(com):
    ent = entriesmap[com.parentid]
    return (ent.publishedraw, com.publishedraw)
comments.sort(key=commentsortkey)

if opts.outdir:
    print('Writing to %s...' % (opts.outdir,))
    os.makedirs(opts.outdir+'/entries', exist_ok=True)
    os.makedirs(opts.outdir+'/comments', exist_ok=True)
    
    entls = []
    for ent in entries:
        entls.append(ent.jsonmap())
        fl = open('%s/entries/%s.html' % (opts.outdir, ent.shortid,), 'w')
        fl.write(ent.content)
        fl.close()

    comls = []
    for com in comments:
        comls.append(com.jsonmap())
        fl = open('%s/comments/%s.html' % (opts.outdir, com.shortid,), 'w')
        fl.write(com.content)
        fl.close()

    map = { 'entries':entls, 'comments':comls }
    fl = open(opts.outdir+'/all.json', 'w')
    json.dump(map, fl, indent=2)
    fl.close()

