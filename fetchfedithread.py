#!/usr/bin/env python3

import sys
import optparse
import re
import json
from html_sanitizer import Sanitizer

popt = optparse.OptionParser()

popt.add_option('-o', '--out',
                action='store', dest='outfile',
                help='write to file')

(opts, args) = popt.parse_args()

if len(args) != 1:
    print('usage: fetchfedithread.py [ URL ] [ -o outfile ]')
    sys.exit(-1)

threadurl = args[0]

match = re.match('(?:.*/)?([0-9]+)$', threadurl)
if not match:
    print('does not look like a thread URL: '+threadurl)
    sys.exit(-1)

threadid = match.group(1)

fl = open('sample-fedi-thread.json')
dat = fl.read()
fl.close()

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
        for el in ls:
            flatls.append(el)
            el['_depth'] = depth
            if '_replies' in el:
                func(el['_replies'], depth+1)
    
    func(idmap[threadid]['_replies'])
    
    for el in flatls:
        published = el['created_at']
        body = el['content']
        depth = el.get('_depth')
        authorname = None
        authoruri = None
        author = el.get('account')
        if author:
            authorname = author.get('display_name')
            authoruri = author.get('url')

        body = sanitizer.sanitize(body)
            
        fl.write('---\n')
        fl.write('published: %s\n' % (published,))
        if depth:
            fl.write('depth: %d\n' % (depth,))
        if authorname:
            fl.write('authorname: %s\n' % (authorname,))
        if authoruri:
            fl.write('authoruri: %s\n' % (authoruri,))
        fl.write('format: html\n')
        fl.write('---\n')
        writeescapedashes(fl, body)
        fl.write('\n')
        
    fl.write('---\n')

obj = json.loads(dat)

if opts.outfile:
    fl = open(opts.outfile, 'w')
    write_comments(obj, fl)
    fl.close()
else:
    write_comments(obj)


