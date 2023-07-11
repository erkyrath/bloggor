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

## How it works

All the files that define the blog are in the `sample` directory.
When you ran the `build.py` script, `-s sample` told it to look there.

Then it wrote all the output to the `site` directory. This already
contains some files needed for proper browsing: `site/css` and `site/js`.

The `servesite.py` runs a simple ad-hoc web server which makes the
`site` directory available as `http://localhost:8001/`.

### The sample directory

The `bloggor.cfg` config file defines the blog's title, server name,
and other such stuff.

The `templates` directory contains [Jinja][] template files. These
define the format of all the blog pages. (Except the RSS/Atom feeds, which
atom built with [feedgenerator][].)

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
as part of an entry page.

### On tidy URLs

The static site generator writes `.html` files. However, all the blog
links use unsuffixed URLs. (`http://localhost:8001/2023/07/welcome` rather
than `http://localhost:8001/2023/07/welcome.html`.) The `welcome.html`
version of the URL works, but we prefer the plain `welcome` version.

Therefore, *your web server must be configured to accept unsuffixed
URLs*. The easiest way to do this is to turn on the [Multiviews][]
feature (for Apache servers).

[Multiviews]: https://httpd.apache.org/docs/2.4/content-negotiation.html

Because I never do anything the easy way, my blog is set up with this
`.htaccess` file instead:

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
