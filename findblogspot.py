#!/usr/bin/env python3

import sys
import re

pat_blogspot = re.compile('["\'](http[s]?://[a-z0-9_.]*(?:googleusercontent|blogspot).com/[^"\']*)["\']', flags=re.IGNORECASE)

allurls = set()

def check(filename):
    fl = open(filename)
    dat = fl.read()
    fl.close()

    ls = pat_blogspot.findall(dat)
    for url in ls:
        allurls.add(url)

for filename in sys.argv[1:]:
    check(filename)
    
ls = list(allurls)
ls.sort()
for url in ls:
    if url.endswith('.html') or url.endswith('.com/'):
        continue
    print(url)
