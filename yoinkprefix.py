import json

obj = json.load(open('rawout/all.json'))
entries = obj['entries']

for ent in entries:
    print(ent['shortid'])
    prefix, _, _ = ent['filename'].rpartition('/')
    prefix = prefix[1:]
    assert(len(prefix) == 7)
    print('  '+prefix)
    print('  '+ent['filename'])
    
