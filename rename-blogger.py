#!/usr/bin/env python3

import sys
import re
import shutil

from readtable import read_table
    
def bytes_to_intarray(dat):
    return [ val for val in dat ]

def intarray_to_bytes(arr):
    return bytes(arr)
    
def parse_png(dat):
    dat = bytes_to_intarray(dat)
    pos = 0
    sig = dat[pos:pos+8]
    pos += 8
    if sig != [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]:
        raise Exception('PNG signature does not match')
    while pos < len(dat):
        clen = (dat[pos] << 24) | (dat[pos+1] << 16) | (dat[pos+2] << 8) | dat[pos+3]
        pos += 4
        ctyp = intarray_to_bytes(dat[pos:pos+4])
        pos += 4
        #print('Chunk:', ctyp, 'len', clen)
        if ctyp == b'IHDR':
            width  = (dat[pos] << 24) | (dat[pos+1] << 16) | (dat[pos+2] << 8) | dat[pos+3]
            pos += 4
            height = (dat[pos] << 24) | (dat[pos+1] << 16) | (dat[pos+2] << 8) | dat[pos+3]
            pos += 4
            return (width, height)
        pos += clen
        pos += 4
    raise Exception('No PNG header block found')

def parse_jpeg(dat):
    dat = bytes_to_intarray(dat)
    #print('Length:', len(dat))
    pos = 0
    while pos < len(dat):
        if dat[pos] != 0xFF:
            raise Exception('marker is not FF')
        while dat[pos] == 0xFF:
            pos += 1
        marker = dat[pos]
        pos += 1
        if marker == 0x01 or (marker >= 0xD0 and marker <= 0xD9):
            #print('FF%02X*' % (marker,))
            continue
        clen = (dat[pos] << 8) | dat[pos+1]
        #print('FF%02X, len %d' % (marker, clen))
        if (marker >= 0xC0 and marker <= 0xCF and marker != 0xC8):
            if clen <= 7:
                raise Exception('SOF block is too small')
            bits = dat[pos+2]
            height = (dat[pos+3] << 8) | dat[pos+4]
            width  = (dat[pos+5] << 8) | dat[pos+6]
            return (width, height)
        pos += clen
    raise Exception('SOF block not found')

class Image:
    def __init__(self, url, tempfile, size):
        self.url = url
        self.tempfile = tempfile
        self.size = size
        self.extra = None

        _, _, val = self.url.rpartition('/')
        if not val or '.' not in val:
            val = tempfile.replace('xx', 'unnamed')
        self.basefile = val
        self.final = self.basefile

    def setextra(self, val):
        self.extra = val
        pre, _, post = self.basefile.rpartition('.')
        self.final = '%s%s.%s' % (pre, val, post,)

    def __repr__(self):
        return '<Image %s (%s)>' % (self.final, self.size,)

urltotempmap = read_table('blogger-image-xxmap')
imagemap = {}

for url, val in urltotempmap.items():
    fl = open('image-blogger/'+val, 'rb')
    dat = fl.read()
    fl.close()
    if val.endswith('.png'):
        size = parse_png(dat)
    elif val.endswith('.jpeg') or val.endswith('.jpg'):
        size = parse_jpeg(dat)
    else:
        raise Exception('unrecognized image')
    
    img = Image(url, val, size)
    imagemap[url] = img

basetoimagemap = {}

for url, img in imagemap.items():
    if img.basefile not in basetoimagemap:
        basetoimagemap[img.basefile] = [ img ]
    else:
        basetoimagemap[img.basefile].append(img)
    
for basefile, ls in basetoimagemap.items():
    ls.sort(key=lambda img:img.size[0]*img.size[1], reverse=True)
    for img in ls[1:]:
        img.setextra('-%sx%s' % img.size)
    
tmpset = set()
for url, img in imagemap.items():
    if img.final in tmpset:
        raise Exception('clash: ' + img.final)
    tmpset.add(img.final)
    print(url)
    print('  '+img.final)
    print('  %dx%d' % img.size)
    #shutil.copyfile('image-blogger/'+img.tempfile, 'image-blogger/'+img.final)
    
