
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

(opts, args) = popt.parse_args()

ctx = bloggor.context.Context(opts)

try:
    ctx.build()
except RuntimeException as ex:
    print('Error: %s' % (ex,))
    sys.exit()

fl = open('pages/home.md')
dat = fl.read()
fl.close()
ctx.mdenv.reset()
body = ctx.mdenv.convert(dat)

fl = open(os.path.join(opts.destdir, 'index.html'), 'w')
template = ctx.jenv.get_template('page.html')
fl.write(template.render(title='Zarf Updates', body=body))
fl.close()
