#!/usr/bin/env python3

import sys
import json

fl = open('out/all.json')
all = json.load(fl)
fl.close()

urimap = {}

for ent in all['entries']:
    urimap[ent['filename']] = ent['shortid']

fl = open('blogger-post-urls')
for ln in fl.readlines():
    ln = ln.strip()
    print(ln)
    res = '???'
    if ln.startswith('http:'):
        ln = ln[ 5 : ]
    elif ln.startswith('https:'):
        ln = ln[ 6 : ]
    if ln.startswith('//blog.zarfhome.com'):
        ln = ln[ 19 : ]
        if ln.endswith('.html'):
            ln = ln[ : -5 ]
        elif ln.endswith('/'):
            ln = ln[ : -1 ]
        key = ln + '.html'
        if key in urimap:
            res = '%s, %s' % (urimap[key], key,)
    print('  '+res)
