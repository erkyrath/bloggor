#!/usr/bin/env python3

import sys
import os
import os.path
import datetime
import optparse

import bloggor.context
from bloggor.excepts import RuntimeException

popt = optparse.OptionParser(usage='build.py [options] [pages...]')

popt.add_option('-s', '--src',
                action='store', dest='srcdir', default='src',
                help='source directory')
popt.add_option('--config',
                action='store', dest='configfile',
                help='config file (default: srcdir/bloggor.cfg)')
popt.add_option('-o', '--out',
                action='store', dest='destdir', default='site',
                help='destination directory')
popt.add_option('-a', '--all',
                action='store_true', dest='buildall',
                help='build all files')
popt.add_option('-r', '--recent',
                action='store', dest='recent', metavar='INTERVAL',
                help='only consider files newer than this ("15m", "1h", etc)')
popt.add_option('--only',
                action='store_true', dest='buildonly',
                help='build only named files (no dependencies)')
popt.add_option('-l', '--long',
                action='store_true', dest='longlist',
                help='list all pages built, even if there\'s lots')
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


ctx = bloggor.context.Context(opts)

tup = datetime.datetime.now(datetime.timezone.utc)
val, _, _ = tup.isoformat().partition('.')
val += 'Z'
print('The time is', val)

success = False

try:
    success = ctx.run(args)
except RuntimeException as ex:
    print('Error: %s' % (ex,))
    sys.exit()

if not success:
    print('Failed!')
else:
    print('Done.')


