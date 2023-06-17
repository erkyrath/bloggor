
import optparse
import os
import os.path

import bloggor.context
from bloggor.page import EntryPage

popt = optparse.OptionParser()

popt.add_option('--src',
                action='store', dest='srcdir', default='.',
                help='source directory')
popt.add_option('-o', '--out',
                action='store', dest='destdir', default='site',
                help='destination directory')

(opts, args) = popt.parse_args()

ctx = bloggor.context.Context()

for dirpath, dirnames, filenames in os.walk(os.path.join(opts.srcdir, 'entries')):
    for filename in filenames:
        if filename.endswith('~'):
            continue
        print(dirpath, filename)
        page = EntryPage(ctx, dirpath, filename)
    


fl = open('pages/home.md')
dat = fl.read()
fl.close()
ctx.mdenv.reset()
body = ctx.mdenv.convert(dat)

fl = open(os.path.join(opts.destdir, 'index.html'), 'w')
template = ctx.jenv.get_template('page.html')
fl.write(template.render(title='Zarf Updates', body=body))
fl.close()
