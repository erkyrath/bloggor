#!/usr/bin/env python3

import sys
import re
import os.path

from readtable import read_table
from bloggor.util import MultiDict

post_name_table = read_table('post-name-table', multi=True)

pat_gameshelf = re.compile('["\'](http[s]?://[a-z0-9_.]*jmac.org/[^"\']*)["\']', flags=re.IGNORECASE)

allurls = MultiDict()

def check(filename):
    shortid = os.path.basename(filename).replace('.html', '')
    prefix, parentpost = post_name_table[shortid]

    fl = open(filename)
    dat = fl.read()
    fl.close()

    ls = pat_gameshelf.findall(dat)
    for url in ls:
        allurls.add(url, (prefix, parentpost))

for filename in sys.argv[1:]:
    check(filename)
    
ls = list(allurls.keys())
ls.sort()
for url in ls:
    prefixls = allurls[url]
    prefixls.sort()
    prefix, parentpost = prefixls[0]
    print(url)
    print('  '+prefix)
    print('  '+parentpost)
    
