import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

class Context:
    def __init__(self):
        self.jenv = Environment(
            loader = FileSystemLoader('templates'),
            autoescape = select_autoescape(),
            keep_trailing_newline = True,
        )

        self.mdenv = markdown.Markdown(extensions=['meta', 'def_list', 'fenced_code', 'tables'])

    
