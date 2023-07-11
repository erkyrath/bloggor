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

The sample site has three posts, plus one more which is in a draft
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
top level. Currently this is `http://localhost:8001/about` and
`http://localhost:8001/comments`.

The `entries` directory contains blog entries, organized by date.
Look in `sample/entries/2023/07`, for example.

Entry files can be HTML (`.html`), Markdown (`.md`), or plain text (`.txt`).
Note that HTML (and HTML in Markdown) is not sanitized! Keeping it clean
and safe is up to you.

All entry files start with a metadata section (delimited by dashes) which
give the entry's title, tags, publication date, and so on. The metadata
must include `live: yes` for the post to be live! Without that line, the
post is only a draft, and will not be indexed or listed.
