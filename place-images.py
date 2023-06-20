#!/usr/bin/env python3

import os.path
import shutil

from readtable import read_table

outdir = 'static/pic'

blogger_image_table = read_table('blogger-image-table', multi=True)
gameshelf_image_table = read_table('gameshelf-image-table', multi=True)

for tup in gameshelf_image_table.values():
    filename, prefix, post = tup
    path = os.path.join('image-gshelf', filename)
    assert os.path.exists(path)
    dest = os.path.join(outdir, prefix, filename)
    os.makedirs(os.path.join(outdir, prefix), exist_ok=True)
    shutil.copyfile(path, dest)

for tup in blogger_image_table.values():
    filename, size, prefix, post = tup
    path = os.path.join('image-blogger', filename)
    assert os.path.exists(path)
    dest = os.path.join(outdir, prefix, filename)
    os.makedirs(os.path.join(outdir, prefix), exist_ok=True)
    shutil.copyfile(path, dest)

