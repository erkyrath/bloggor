
import sys
import os
import os.path
import optparse

import bloggor.context
from bloggor.excepts import RuntimeException

popt = optparse.OptionParser()

popt.add_option('--src',
                action='store', dest='srcdir', default='.',
                help='source directory')
popt.add_option('-o', '--out',
                action='store', dest='destdir', default='site',
                help='destination directory')
popt.add_option('--nocommit',
                action='store_true', dest='nocommit',
                help='do not commit tmp.html files')

(opts, args) = popt.parse_args()

ctx = bloggor.context.Context(opts)

try:
    ctx.build()
except RuntimeException as ex:
    print('Error: %s' % (ex,))
    sys.exit()

