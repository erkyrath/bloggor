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
print('###', threadid)

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

    ### sort on 'in_reply_to_id'
    
    for el in obj['descendants']:
        published = el['created_at']
        body = el['content']
        authorname = None
        authoruri = None
        author = el.get('account')
        if author:
            authorname = author.get('display_name')
            authoruri = author.get('url')

        body = sanitizer.sanitize(body)
            
        fl.write('---\n')
        fl.write('published: %s\n' % (published,))
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


