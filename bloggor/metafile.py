import re

# Copied from markdown.extensions.meta.

META_RE = re.compile(r'^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)')
META_MORE_RE = re.compile(r'^[ ]{4,}(?P<value>.*)')
BEGIN_RE = re.compile(r'^-{3}(\s.*)?')
END_RE = re.compile(r'^(-{3}|\.{3})(\s.*)?')

class MetaFile:
    def __init__(self, filename=None, stream=None, init=None):
        self.filename = filename
        self.stream = stream
        if init is not None:
            self.content, self.meta = init
            return
        if filename and stream:
            raise Exception('cannot supply both filename and stream')
        if not filename and not stream:
            raise Exception('must supply either filename or stream')
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
                if ln.strip() == '' or END_RE.match(ln):
                    # blank line or end of YAML header - done
                    break
                m1 = META_RE.match(ln)
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

pat_dashes = re.compile(r'^(---+)\s*$')

class MultiMetaFile:
    def __init__(self, filename=None, stream=None):
        self.filename = filename
        self.stream = stream
        if filename and stream:
            raise Exception('cannot supply both filename and stream')
        self.ls = None
    
    def read(self):
        if self.ls is not None:
            return self.ls

        self.ls = []

        if self.stream:
            fl = self.stream
        else:
            fl = open(self.filename)

        ln = fl.readline()
        match = pat_dashes.match(ln)
        if not match:
            raise Exception('not a MultiMetaFile')
        count = len(match.group(1))

        done = False
        while not done:
            meta = {}
            body = []
            
            while True:
                ln = fl.readline()
                if ln.strip() == '':
                    # blank line - done
                    break
                match = pat_dashes.match(ln)
                if match:
                    # end of YAML header - done
                    count = len(match.group(1))
                    break
                m1 = META_RE.match(ln)
                if m1:
                    key = m1.group('key').lower().strip()
                    value = m1.group('value').strip()
                    try:
                        meta[key].append(value)
                    except KeyError:
                        meta[key] = [value]
                else:
                    m2 = META_MORE_RE.match(ln)
                    if m2 and key:
                        # Add another line to existing key
                        meta[key].append(m2.group('value').strip())
                    else:
                        body.append(ln)
                        break  # no meta data - done
            
            while True:
                ln = fl.readline()
                if not ln:
                    done = True
                    break
                match = pat_dashes.match(ln)
                if match and len(match.group(1)) == count:
                    break
                body.append(ln)

            if body or meta:
                self.ls.append( (''.join(body), meta) )
            
        if fl != self.stream:
            fl.close()

        return self.ls


def ls_as_bool(ls, default=False):
    if not ls:
        return default
    if len(ls) > 1:
        raise ValueError('not a single value')
    val = ls[0].strip()
    val = val.lower()
    if val in ('t', 'true', 'y', 'yes'):
        return True
    if val in ('f', 'false', 'n', 'no'):
        return False
    raise ValueError('not a boolean value')

def ls_as_value(ls):
    if not ls:
        return None
    if len(ls) > 1:
        raise ValueError('not a single value')
    return ls[0].strip()


