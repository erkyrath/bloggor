#!/usr/bin/env python3

import sys
import json

fl = open('tmpout/all.json')
all = json.load(fl)
fl.close()

urimap = {}

for ent in all['entries']:
    urimap[ent['filename']] = ent['shortid']

fl = open('gameshelf-post-urls')
for ln in fl.readlines():
    ln = ln.strip()
    print(ln)
    res = ('???', '???')
    if ln.startswith('http://gameshelf.jmac.org'):
        ln = ln[ 25 : ]
        if ln.endswith('.html'):
            ln = ln[ : -5 ]
        elif ln.endswith('/'):
            ln = ln[ : -1 ]
        key = ln + '.html'
        if key in urimap:
            res = (urimap[key], key)
        else:
            prefix = ln[ 0 : 30 ]
            for key in urimap:
                if key.startswith(prefix):
                    res = (urimap[key], key)
                    break
    print('  '+res[0])
    print('  '+res[1])
