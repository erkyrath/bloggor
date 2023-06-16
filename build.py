
import optparse
import os
import os.path
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

popt = optparse.OptionParser()

popt.add_option('-o', '--out',
                action='store', dest='sitedir', default='site',
                help='site directory')

(opts, args) = popt.parse_args()

jenv = Environment(
    loader = FileSystemLoader('templates'),
    autoescape = select_autoescape(),
    keep_trailing_newline = True,
)

mdenv = markdown.Markdown()

fl = open('pages/home.md')
dat = fl.read()
fl.close()
mdenv.reset()
body = mdenv.convert(dat)

fl = open(os.path.join(opts.sitedir, 'index.html'), 'w')
template = jenv.get_template('page.html')
fl.write(template.render(title='Zarf Updates', body=body))
fl.close()
