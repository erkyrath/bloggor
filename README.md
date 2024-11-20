# Bloggor: a static blog site generator

- Designed by Andrew Plotkin <erkyrath@eblong.com>

This is a very simple blog generator tool. I use it to maintain
[my personal blog](https://blog.zarfhome.com/).

If you want a static site generator, you probably don't want this one.
Bloggor is uncommented, undocumented, and supported only in that I
keep tweaking it to suit my whims.
Have you instead considered...

- [Zola](https://www.getzola.org/)?
- [Pelican](https://getpelican.com/)?
- [Metalsmith](https://metalsmith.io/)?

But if you want to mess around with Bloggor, feel free!

## Try it out

Type these commands:

```
python build.py -a -s sample
python servesite.py
```

Then visit `http://localhost:8001/` in your web browser. Lookit! Blog!

The sample site has four posts, plus one more which is in a draft
state. You can view the draft post at
`http://localhost:8001/2023/07/unfinished`, but it is not listed
on the blog's front page (or in the feeds).

## Usage

```
python3 build.py [ OPTIONS ] [ FILES TO BUILD ]
```

- `-s DIR`, `--src DIR` : The source directory. Default is `src`.
`sample` in this repository is an example of a working source directory.
- `-o DIR`, `--out DIR` : The output directory. Default is `site`.
Will be created if it does not exist.
- `--config CONFIGFILE` : The configuration file. Default is
`SRCDIR/bloggor.cfg`.
- `-a`, `--all` : Build all files.
- `-l`, `--long` : List all files built, even if there's lots of them.
- `--only` : Build only the named files, not dependencies.
- `--dry` : Read the source files but do not write anything.

To rebuild the whole site, use `-a`. To rebuild only specific pages,
name them. For example:

```
python build.py -s sample unfinished.md
python build.py -s sample history tags
python build.py -s sample '2023/07/*'
```

The format for naming pages is flexible, and even supports wildcards
(as shown).

When you rebuild a page, the script automatically rebuilds pages that
mention it. So if you rebuild an entry page, the tags, history,
and RSS feed pages will be updated as well. This ensures that the
blog indexes are always complete.

However, this dependency feature only looks at files that exist. It can't
tell if you *delete* a page, or delete tags from a page. So if you do
anything like that, re-run the script with `-a`. You might want to run
with `-a` once a month just in case.

## How it works

All the files that define the blog are in the source directory.
When you ran the `build.py` script, `-s sample` told it to look in
the `sample` directory for these files.

Then it wrote all the output to the `site` directory. This already
contains some files needed for proper browsing: `site/css` and `site/js`.

The `servesite.py` runs a simple ad-hoc web server which makes the
`site` directory available as `http://localhost:8001/`.

### The source directory

The `bloggor.cfg` config file defines the blog's title, server name,
and other such stuff.

The `templates` directory contains [Jinja][] template files. These
define the format of all the blog pages. (Except the RSS/Atom feeds, which
are built with [feedgenerator][].)

[Jinja]: https://jinja.palletsprojects.com/en/3.1.x/
[feedgenerator]: https://pypi.org/project/feedgenerator/

The `pages` directory contains static pages which appear at the blog's
top level. Currently there are two of these:
`http://localhost:8001/about` and `http://localhost:8001/comments`.

The `entries` directory contains blog entries, organized by date.
Look in `sample/entries/2023/07`, for example.

Entry files can be HTML (`.html`), Markdown (`.md`), or plain text (`.txt`).
Note that HTML (and HTML in Markdown) is not sanitized! Keeping it clean
and safe is up to you.

All entry files start with a metadata section (delimited by dashes) which
give the entry's title, tags, publication date, and so on. The metadata
must include `live: yes` for the post to be live! Without that line, the
post is only a draft, and will not be indexed or listed.

A file with the `.comments` extension is a list of comments to be displayed
as part of an entry page. This is a list of metadata/body sections, again
delimited by dashes. See `sample/entries/2023/07/commented-post.comments`.

### On tidy URLs

The static site generator writes `.html` files. However, all the blog
links use unsuffixed URLs. (`http://localhost:8001/2023/07/welcome` rather
than `http://localhost:8001/2023/07/welcome.html`.) The `welcome.html`
version of the URL works, but we prefer the plain `welcome` version.

Therefore, *your web server must be configured to accept unsuffixed
URLs*. Otherwise all the blog links will yell 404.

The `servesite.py` script is configured this way for local testing.

On an Apache server, the easiest way to make this work is to turn on the
[Multiviews][] feature.

[Multiviews]: https://httpd.apache.org/docs/2.4/content-negotiation.html

Because I never do anything the easy way, my blog is set up with this
`.htaccess` file:

```
RewriteEngine On
RewriteCond %{REQUEST_URI} [^/]$
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteCond %{REQUEST_FILENAME}\.html -f
RewriteRule ^(.+)$ $1\.html [last]
```

Also, in the `feeds/posts` directory:

```
RewriteEngine On
RewriteRule ^default$ default.xml [last]
```

### On Markdown

Markdown has never exactly been *standardized*, so I did not hesitate
to customize the Markdown flavor used by Bloggor.

The [metadata][meta], [attribute list][attr_list],
[definition list][def_list], [fenced code][fenced], and [tables][tables]
extensions are turned on.

[attr_list]: https://python-markdown.github.io/extensions/attr_list/
[meta]: https://python-markdown.github.io/extensions/meta_data/
[def_list]: https://python-markdown.github.io/extensions/definition_lists/
[fenced]: https://python-markdown.github.io/extensions/fenced_code_blocks/
[tables]: https://python-markdown.github.io/extensions/tables/

A line that looks like `- - -` (spaced dashes) indicates the "fold".
Text below this will not appear on the blog's front page; instead there
will be a "Read the rest..." link.

A block in triple braces will retain line breaks:

```
{{{
*Five* short lines
Iambic pace
It's like haiku
But for your face
BURMA SHAVE
}}}
```

Or you can create a div with any class (this is more or less the [attr_list][attr_list] extension):

```
{{{ { .Center }
Stuff here.
}}}
```

Markdown has a format for images and image links, but I decided I hate it, so now I use this. (All lines but `img:` are optional.) Note that even though this is multiline construct, it creates one inline image or link.

```
{{:
  img: /pic/bar-s.png
  link: https://eblong.com/whatever
  alt: Here's your alt text.
  width: 200
  height: 100
:}}
```

Links (including image links) that start with your blog URL will be
changed to server-relative links. (Except in the RSS feed, of course.)
This aids site portability.

## How to customize Bloggor

First, edit `bloggor.cfg` and fill in your info.

Then get into the `templates` and `site/css/page.css`. Go wild.

