#!/usr/bin/env python3

import sys
import re

pat_blogzarf = re.compile('["\'](http[s]?://blog.zarfhome.com/[^"\']*)["\']', flags=re.IGNORECASE)

allurls = set()

def check(filename):
    fl = open(filename)
    dat = fl.read()
    fl.close()

    ls = pat_blogzarf.findall(dat)
    for url in ls:
        allurls.add(url)

for filename in sys.argv[1:]:
    check(filename)
    
ls = list(allurls)
ls.sort()
for url in ls:
    print(url)