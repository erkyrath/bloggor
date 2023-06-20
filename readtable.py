import re

pat_indent = re.compile('^[ \t]+')
    

def read_table(filename, multi=False):
    map = {}
    key = None
    fl = open(filename)
    for ln in fl.readlines():
        match = pat_indent.match(ln)
        if not match:
            key = ln.strip()
        else:
            if not multi:
                if key in map:
                    raise Exception('duplicate key: ' + key)
                map[key] = ln.strip()
            else:
                if key not in map:
                    map[key] = [ ln.strip() ]
                else:
                    map[key].append(ln.strip())
    return map
