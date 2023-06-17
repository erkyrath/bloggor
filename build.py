
import optparse
import os
import os.path
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

popt = optparse.OptionParser()

popt.add_option('--src',
                action='store', dest='srcdir', default='.',
                help='source directory')
popt.add_option('-o', '--out',
                action='store', dest='destdir', default='site',
                help='destination directory')

(opts, args) = popt.parse_args()

jenv = Environment(
    loader = FileSystemLoader('templates'),
    autoescape = select_autoescape(),
    keep_trailing_newline = True,
)

for dirpath, dirnames, filenames in os.walk(os.path.join(opts.srcdir, 'entries')):
    for filename in filenames:
        if filename.endswith('~'):
            continue
        print(dirpath, filename)
    

mdenv = markdown.Markdown(extensions=['meta', 'def_list', 'fenced_code', 'tables'])

fl = open('pages/home.md')
dat = fl.read()
fl.close()
mdenv.reset()
body = mdenv.convert(dat)

fl = open(os.path.join(opts.destdir, 'index.html'), 'w')
template = jenv.get_template('page.html')
fl.write(template.render(title='Zarf Updates', body=body))
fl.close()
