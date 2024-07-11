#!/usr/bin/env python3

import sys
import optparse
import os, os.path
import re
import json
import urllib.request
from html_sanitizer import Sanitizer

popt = optparse.OptionParser()

popt.add_option('--inclusive',
                action='store_true', dest='inclusive',
                help='include the named post as well as its descendants')
popt.add_option('-o', '--out',
                action='store', dest='outfile',
                help='write to file')
popt.add_option('-a', '--append',
                action='store', dest='appendfile',
                help='append to file')
popt.add_option('--attach', '--attachdir',
                action='store', dest='attachdir',
                help='fetch attachments to this dir')
popt.add_option('--server',
                action='store', dest='server', default='mastodon.gamedev.place',
                help='Mastodon server')

(opts, args) = popt.parse_args()

if len(args) != 1:
    print('usage: fetchfedithread.py [ URL ] [ -o outfile ]')
    sys.exit(-1)

if opts.outfile and opts.appendfile:
    print('cannot use both -o and -a')
    sys.exit(-1)
    
threadurl = args[0]

match = re.match('(?:.*/)?([0-9]+)$', threadurl)
if not match:
    print('does not look like a thread URL: '+threadurl)
    sys.exit(-1)

threadid = match.group(1)

fetchurl = 'https://'+opts.server+'/api/v1/statuses/'+threadid;
print(fetchurl)

try:
    req = urllib.request.urlopen(fetchurl+'/context')
    dat = req.read()
    basedat = None
    if opts.inclusive:
        req = urllib.request.urlopen(fetchurl)
        basedat = req.read()
except Exception as ex:
    print(str(ex))
    sys.exit(-1)

sanitizer = Sanitizer({ 'add_nofollow': True })

pat_dashes = re.compile(r'^(---+)\s*$')

def writeescapedashes(fl, text, delim=3):
    ls = text.split('\n')
    for ln in ls:
        match = pat_dashes.match(ln)
        if match and len(match.group(1)) == delim:
            ln = '-' + ln
        fl.write(ln+'\n')

def write_comments(ells, fl=sys.stdout):
    idmap = {}

    if not opts.inclusive:
        idmap[threadid] = { '_replies':[] }
    
    for el in ells:
        id = el['id']
        idmap[id] = el

    for el in ells:
        parid = el['in_reply_to_id']
        if parid is None:
            continue
        if parid not in idmap:
            continue
        par = idmap[parid]
        if '_replies' not in par:
            par['_replies'] = [ el ]
        else:
            par['_replies'].append(el)

    flatls = []

    def func(ls, depth=0):
        ls.sort(key=lambda el:el['created_at'])
        for el in ls:
            flatls.append(el)
            el['_depth'] = depth
            if '_replies' in el:
                func(el['_replies'], depth+1)

    if not opts.inclusive:
        func(idmap[threadid]['_replies'])
    else:
        func([ idmap[threadid] ])
    
    for el in flatls:
        id = el['id']
        published = el['created_at']
        body = el['content']
        depth = el.get('_depth')
        fediurl = el.get('url')
        authorname = None
        authoruri = None
        author = el.get('account')
        if author:
            authorname = author.get('display_name')
            if not authorname:
                authorname = author.get('username')
            authoruri = author.get('url')

        body = sanitizer.sanitize(body)

        attachls = []
        atells = el.get('media_attachments')
        if atells:
            atells = [ atel for atel in atells if atel.get('url') ]
        if atells:
            for ix, atel in enumerate(atells):
                at = {
                    'index': ix,
                    'id': '%s_%s' % (id, ix,),
                    'url': atel['url'],
                    'preview_url': atel.get('preview_url'),
                    'description': atel.get('description'),
                }
                _, _, val = at['url'].rpartition('.')
                at['localfile'] = 'attach_%s_%s.%s' % (id, ix, val,)
                if opts.attachdir:
                    at['localpath'] = os.path.join(opts.attachdir, at['localfile'])
                aspect = None
                if atel.get('meta') and atel['meta'].get('original'):
                    aspect = atel['meta']['original'].get('aspect')
                if atel.get('meta') and atel['meta'].get('small'):
                    aspect = atel['meta']['small'].get('aspect')
                at['aspect'] = aspect
                attachls.append(at)
        el['_attachls'] = attachls
            
        fl.write('---\n')
        fl.write('fediid: %s\n' % (id,))
        if fediurl:
            fl.write('fediurl: %s\n' % (fediurl,))
        fl.write('published: %s\n' % (published,))
        if depth:
            fl.write('depth: %d\n' % (depth,))
        if authorname:
            fl.write('authorname: %s\n' % (authorname,))
        if authoruri:
            fl.write('authoruri: %s\n' % (authoruri,))
        if attachls:
            fl.write('attachcount: %s\n' % (len(attachls),))
            for at in attachls:
                ix = at['index']
                fl.write('attach_%s_url: %s\n' % (ix, at['url'],))
                fl.write('attach_%s_localfile: %s\n' % (ix, at['localfile'],))
                if at.get('localpath'):
                    fl.write('attach_%s_localpath: %s\n' % (ix, at['localpath'],))
                if at.get('preview_url'):
                    fl.write('attach_%s_previewurl: %s\n' % (ix, at['preview_url'],))
                if at.get('description'):
                    fl.write('attach_%s_description: %s\n' % (ix, at['description'],))
                if at.get('aspect'):
                    fl.write('attach_%s_aspect: %s\n' % (ix, at['aspect'],))
        fl.write('format: html\n')
        fl.write('source: mastodon\n')
        fl.write('---\n')
        writeescapedashes(fl, body)
        fl.write('\n')
        
    fl.write('---\n')

    for el in flatls:
        for at in el['_attachls']:
            prevurl = at.get('preview_url')
            locpath = at.get('localpath')
            if prevurl and locpath:
                try:
                    req = urllib.request.urlopen(prevurl)
                    dat = req.read()
                    atfl = open(locpath, 'wb')
                    atfl.write(dat)
                    atfl.close()
                    print('Fetched %s to %s' % (at['id'], locpath,))
                except Exception as ex:
                    print(str(ex))
    
    idls = [ el['id'] for el in flatls ]
    attachids = [ at['id'] for el in flatls for at in el['_attachls'] ]
    print('%d comments found: %s' % (len(flatls), ', '.join(idls)))
    if attachids:
        print('%d attachments found: %s' % (len(attachids), ', '.join(attachids)))

obj = json.loads(dat)
ells = obj.get('descendants')

if basedat:
    obj = json.loads(basedat)
    ells.insert(0, obj)
    
obj = None

if not ells:
    print('no comments')
    sys.exit()

if opts.outfile:
    fl = open(opts.outfile, 'w')
    write_comments(ells, fl)
    fl.close()
elif opts.appendfile:
    fl = open(opts.appendfile, 'a')
    write_comments(ells, fl)
    fl.close()
else:
    write_comments(ells)


