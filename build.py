
import sys
import os
import os.path
import optparse

import bloggor.context
from bloggor.excepts import RuntimeException

popt = optparse.OptionParser()

popt.add_option('-s', '--src',
                action='store', dest='srcdir', default='src',
                help='source directory')
popt.add_option('-o', '--out',
                action='store', dest='destdir', default='site',
                help='destination directory')
popt.add_option('--serverurl',
                action='store', dest='serverurl', default='https://blog.zarfhome.com/',
                help='canonical server URL (ending with slash)')
popt.add_option('--dry', '--dryrun',
                action='store_true', dest='dryrun',
                help='read source but do not generate')
popt.add_option('--nocommit',
                action='store_true', dest='nocommit',
                help='do not commit tmp.html files')
popt.add_option('--notemp',
                action='store_true', dest='notemp',
                help='write output files with no tmp.html stage')

(opts, args) = popt.parse_args()

if args:
    print('usage: build.py [ options ]')
    sys.exit()

ctx = bloggor.context.Context(opts)

success = False

try:
    success = ctx.build()
except RuntimeException as ex:
    print('Error: %s' % (ex,))
    sys.exit()

if not success:
    print('Failed!')
else:
    print('Done.')


