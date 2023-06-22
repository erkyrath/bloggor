import re

# Copied from markdown.extensions.meta.

META_RE = re.compile(r'^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)')
META_MORE_RE = re.compile(r'^[ ]{4,}(?P<value>.*)')
BEGIN_RE = re.compile(r'^-{3}(\s.*)?')
END_RE = re.compile(r'^(-{3}|\.{3})(\s.*)?')

class MetaFile:
    def __init__(self, filename=None, stream=None):
        self.filename = filename
        self.stream = stream
        if filename and stream:
            raise Exception('cannot supply both filename and stream')
        self.content = None
        self.meta = None

    def read(self):
        if self.content is not None:
            return self.content, self.meta
        
        self.meta = {}
        self.content = ''

        if self.stream:
            fl = self.stream
        else:
            fl = open(self.filename)
        
        ln = fl.readline()
        if not BEGIN_RE.match(ln):
            self.content = ln
        else:
            while True:
                ln = fl.readline()
                m1 = META_RE.match(ln)
                if ln.strip() == '' or END_RE.match(ln):
                    # blank line or end of YAML header - done
                    break
                if m1:
                    key = m1.group('key').lower().strip()
                    value = m1.group('value').strip()
                    try:
                        self.meta[key].append(value)
                    except KeyError:
                        self.meta[key] = [value]
                else:
                    m2 = META_MORE_RE.match(ln)
                    if m2 and key:
                        # Add another line to existing key
                        self.meta[key].append(m2.group('value').strip())
                    else:
                        self.content = ln
                        break  # no meta data - done
        self.content += fl.read()

        if fl != self.stream:
            fl.close()

        return self.content, self.meta

