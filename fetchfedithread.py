#!/usr/bin/env python3

import sys
import optparse
import re
import json
import urllib.request
from html_sanitizer import Sanitizer

popt = optparse.OptionParser()

popt.add_option('-o', '--out',
                action='store', dest='outfile',
                help='write to file')
popt.add_option('-a', '--append',
                action='store', dest='appendfile',
                help='append to file')
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

fetchurl = 'https://'+opts.server+'/api/v1/statuses/'+threadid+'/context';
print(fetchurl)

try:
    req = urllib.request.urlopen(fetchurl)
    dat = req.read()
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

def write_comments(obj, fl=sys.stdout):
    ells = obj.get('descendants')
    if not ells:
        print('no comments')
        return

    idmap = {}
    idmap[threadid] = { '_replies':[] }
    
    for el in obj['descendants']:
        id = el['id']
        idmap[id] = el

    for el in obj['descendants']:
        parid = el['in_reply_to_id']
        if parid not in idmap:
            raise Exception('message %s in reply to %s, which is not known' % (el['id'], parid))
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
    
    func(idmap[threadid]['_replies'])
    
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
                    'url': atel['url'],
                    'preview_url': atel.get('preview_url'),
                    'description': atel.get('description'),
                }
                _, _, val = at['url'].rpartition('.')
                at['localfile'] = 'attach_%s_%s.%s' % (id, ix, val,)
                aspect = None
                if atel.get('meta') and atel['meta'].get('original'):
                    aspect = atel['meta']['original'].get('aspect')
                if atel.get('meta') and atel['meta'].get('small'):
                    aspect = atel['meta']['small'].get('aspect')
                at['aspect'] = aspect
                if at.get('url'):
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

    idls = [ el['id'] for el in flatls ]
    print('%d comments found: %s' % (len(flatls), ', '.join(idls)))
    attachcounts = [ len(el['_attachls']) for el in flatls ]
    val = sum(attachcounts)
    if val:
        print('%d total attachments' % (val,))

obj = json.loads(dat)

if opts.outfile:
    fl = open(opts.outfile, 'w')
    write_comments(obj, fl)
    fl.close()
elif opts.appendfile:
    fl = open(opts.appendfile, 'a')
    write_comments(obj, fl)
    fl.close()
else:
    write_comments(obj)


