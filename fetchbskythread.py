#!/usr/bin/env python3

import sys
import optparse
import os, os.path
import re
import json
import configparser

import atproto
from atproto.exceptions import BadRequestError

popt = optparse.OptionParser()

popt.add_option('--inclusive',
                action='store_true', dest='inclusive',
                help='include the named post as well as its descendants')
popt.add_option('-o', '--out',
                action='store', dest='outfile',
                help='write to file')
popt.add_option('-a', '--append',
                action='store', dest='appendfile',
                help='append to file')
popt.add_option('--attach', '--attachdir',
                action='store', dest='attachdir',
                help='fetch attachments to this dir')

(opts, args) = popt.parse_args()

if len(args) != 1:
    print('usage: fetchbskythread.py [ URL ] [ -o/-a outfile ] [ --attach dir ]')
    sys.exit(-1)

if opts.outfile and opts.appendfile:
    print('cannot use both -o and -a')
    sys.exit(-1)

if opts.attachdir:
    print('--attachdir not implemented')
    sys.exit(-1)

configpath = os.path.join(os.environ['HOME'], '.config/bsky.cfg')
config = configparser.ConfigParser()
config.read(configpath)

bsky_userid = config['DEFAULT']['userid']
bsky_password = config['DEFAULT']['password']

threadurl = args[0]

match = re.match('(?:.*/)?([0-9a-z]+)$', threadurl)
if not match:
    print('does not look like a thread URL: '+threadurl)
    sys.exit(-1)

threadid = match.group(1)

client = atproto.Client()

try:
    profile = client.login(bsky_userid, bsky_password)
    origpost = client.get_post(threadid)
    thread = client.get_post_thread(origpost.uri)
except BadRequestError as ex:
    print('%s: %s' % (ex.response.content.error, ex.response.content.message,))
    sys.exit(-1)
except Exception as ex:
    print(str(ex))
    sys.exit(-1)

def scan_post(tvp, ells, depth=0):
    _, _, fediid = tvp.post.uri.rpartition('/')
    fediurl = 'https://bsky.app/profile/%s/post/%s' % (tvp.post.author.handle, fediid)
    authorurl = 'https://bsky.app/profile/%s' % (tvp.post.author.handle,)
    el = {
        'id': fediid,
        'url': fediurl,
        'display_name': tvp.post.author.display_name,
        'authorurl': authorurl,
        'handle': tvp.post.author.handle,
        'published': tvp.post.record.created_at,
        '_depth': depth,
        'content': tvp.post.record.text,
    }
    ells.append(el)
    for subtvp in tvp.replies:
        scan_post(subtvp, ells, depth+1)
    
pat_dashes = re.compile(r'^(---+)\s*$')

def writeescapedashes(fl, text, delim=3):
    ls = text.split('\n')
    for ln in ls:
        match = pat_dashes.match(ln)
        if match and len(match.group(1)) == delim:
            ln = '-' + ln
        fl.write(ln+'\n')

def write_comments(ells, fl=sys.stdout):    
    for el in ells:
        id = el['id']
        published = el['published']
        body = el['content']
        depth = el.get('_depth')
        fediurl = el.get('url')
        authorname = el.get('display_name')
        authoruri = el.get('authorurl')

        fl.write('---\n')
        fl.write('fediid: %s\n' % (id,))
        if fediurl:
            fl.write('fediurl: %s\n' % (fediurl,))
        fl.write('published: %s\n' % (published,))
        if depth:
            fl.write('depth: %d\n' % (depth,))
        if authorname:
            fl.write('authorname: %s\n' % (authorname,))
        if authoruri:
            fl.write('authoruri: %s\n' % (authoruri,))
        fl.write('format: txt\n')
        fl.write('source: bluesky\n')
        fl.write('---\n')
        writeescapedashes(fl, body)
        fl.write('\n')
        
    fl.write('---\n')

    idls = [ el['id'] for el in ells ]
    print('%d comments found: %s' % (len(idls), ', '.join(idls)))

ells = []
if opts.inclusive:
    scan_post(thread.thread, ells)
else:
    for tvp in thread.thread.replies:
        scan_post(tvp, ells)

if not ells:
    print('no comments')
    sys.exit()

if opts.outfile:
    fl = open(opts.outfile, 'w')
    write_comments(ells, fl)
    fl.close()
elif opts.appendfile:
    fl = open(opts.appendfile, 'a')
    write_comments(ells, fl)
    fl.close()
else:
    write_comments(ells)


