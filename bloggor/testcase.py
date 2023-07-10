import unittest
import datetime
import io

from .constants import FileType, parse_filetype
from .constants import Depend, parse_depend
from .util import parsespecs
from .util import tagfilename
from .util import parsedate
from .util import relativetime
from .util import xofypages
from .util import absolutizeurls
from .metafile import MetaFile
from .metafile import MultiMetaFile
from .pages import PageSet

# Run me with:
#    python3 -m bloggor.testcase

class TestFileType(unittest.TestCase):
    def test(self):
        self.assertEqual(parse_filetype('txt'), FileType.TXT)
        self.assertEqual(parse_filetype('TXT'), FileType.TXT)
        self.assertEqual(parse_filetype('Txt'), FileType.TXT)
        self.assertEqual(parse_filetype('text'), FileType.TXT)
        self.assertEqual(parse_filetype('TEXT'), FileType.TXT)

        self.assertEqual(parse_filetype('md'), FileType.MD)
        self.assertEqual(parse_filetype('html'), FileType.HTML)
        self.assertEqual(parse_filetype('whtml'), FileType.WHTML)

    def test_bad(self):
        self.assertRaises(ValueError, parse_filetype, 'foo')
        

class TestDepend(unittest.TestCase):
    def test(self):
        self.assertEqual(parse_depend('body'), Depend.BODY)
        self.assertEqual(parse_depend('BODY'), Depend.BODY)

        self.assertEqual(parse_depend('tag'), Depend.TAGS)
        self.assertEqual(parse_depend('tags'), Depend.TAGS)

        self.assertEqual(parse_depend('all'), Depend.ALL)
        self.assertEqual(parse_depend('none'), Depend.NONE)
        
        self.assertEqual(parse_depend('body,title,pubdate'), Depend.BODY|Depend.TITLE|Depend.PUBDATE)

    def test_bad(self):
        self.assertRaises(ValueError, parse_depend, 'foo')
        

class TestParseSpecs(unittest.TestCase):
    def test(self):
        ls = parsespecs([])
        self.assertEqual(ls, [])
        
        ls = parsespecs(['one', 'two', 'three'])
        self.assertEqual(ls, [('one', Depend.ALL), ('two', Depend.ALL), ('three', Depend.ALL)])
        
        ls = parsespecs(['/one/two', '/three'])
        self.assertEqual(ls, [('one/two', Depend.ALL), ('three', Depend.ALL)])
        
        ls = parsespecs(['one:title', 'two:TAG'])
        self.assertEqual(ls, [('one', Depend.TITLE), ('two', Depend.TAGS)])

        ls = parsespecs(['one:title,body', 'two:all'])
        self.assertEqual(ls, [('one', Depend.TITLE|Depend.BODY), ('two', Depend.ALL)])
        
    def test_bad(self):
        self.assertRaises(ValueError, parsespecs, ['/'])
        
    
class TestTagFilename(unittest.TestCase):
    def test(self):
        self.assertEqual(tagfilename(''), '==')
        self.assertEqual(tagfilename('foo'), 'foo')
        self.assertEqual(tagfilename('foo bar'), 'foo_bar')
        self.assertEqual(tagfilename('mr. robot'), 'mr=2E=_robot')
        self.assertEqual(tagfilename('_='), '=5F==3D=')
        self.assertEqual(tagfilename('\u03B1'), '=3B1=')
        self.assertEqual(tagfilename('\u03B1\u03B2\u03B3x'), '=3B1==3B2==3B3=x')
        self.assertEqual(tagfilename('\u623F'), '=623F=')
        self.assertEqual(tagfilename('\U0001F600'), '=1F600=')


class TestParseDate(unittest.TestCase):

    def test_good(self):
        val = parsedate('2023-05-01')
        self.assertEqual(val, '2023-05-01T12:00:00+00:00')
        self.assertEqual(parsedate(val), val)

        val = parsedate('2011-05-24T16:35:40')
        self.assertEqual(val, '2011-05-24T16:35:40+00:00')
        self.assertEqual(parsedate(val), val)

        val = parsedate('2011-05-24T16:35:40Z')
        self.assertEqual(val, '2011-05-24T16:35:40+00:00')
        self.assertEqual(parsedate(val), val)

        val = parsedate('2011-05-24T16:35:40+00:00')
        self.assertEqual(val, '2011-05-24T16:35:40+00:00')
        self.assertEqual(parsedate(val), val)

        val = parsedate('2011-05-24T16:35:40.123')
        self.assertEqual(val, '2011-05-24T16:35:40+00:00')
        self.assertEqual(parsedate(val), val)

        val = parsedate('2011-05-24T16:35:40.123+00:00')
        self.assertEqual(val, '2011-05-24T16:35:40+00:00')
        self.assertEqual(parsedate(val), val)

    def test_bad(self):
        self.assertRaises(ValueError, parsedate, None)
        self.assertRaises(ValueError, parsedate, '')
        self.assertRaises(ValueError, parsedate, '2023-05-1')
        self.assertRaises(ValueError, parsedate, '2023-5-01')
        self.assertRaises(ValueError, parsedate, '2023-05-01T12:00:00-00:00')
        self.assertRaises(ValueError, parsedate, '2023-05-01T12:00:00+05:00')
        self.assertRaises(ValueError, parsedate, '2023-05-01 12:00:00+00:00')

class TestRelativeTime(unittest.TestCase):
    def test(self):
        fromiso = datetime.datetime.fromisoformat
        
        d1 = fromiso('2023-05-01T12:00:00+00:00')
        
        d2 = fromiso('2023-05-01T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'straightaway')

        d2 = fromiso('2023-05-01T11:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'straightaway')

        d2 = fromiso('2023-04-30T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'straightaway')

        d2 = fromiso('2023-04-30T12:10:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'straightaway')

        d2 = fromiso('2023-05-01T12:20:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'straightaway')

        d2 = fromiso('2023-05-01T12:40:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'straightaway')

        d2 = fromiso('2023-05-01T13:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), '1 hour later')

        d2 = fromiso('2023-05-01T13:20:00+00:00')
        self.assertEqual(relativetime(d2, d1), '1 hour later')

        d2 = fromiso('2023-05-01T13:50:00+00:00')
        self.assertEqual(relativetime(d2, d1), '2 hours later')

        d2 = fromiso('2023-05-01T14:20:00+00:00')
        self.assertEqual(relativetime(d2, d1), '2 hours later')

        d2 = fromiso('2023-05-02T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), '1 day later')

        d2 = fromiso('2023-05-03T10:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), '2 days later')

        d2 = fromiso('2023-05-03T14:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), '2 days later')

        d2 = fromiso('2023-05-08T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), '7 days later')

        d2 = fromiso('2023-05-09T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'May 9')

        d2 = fromiso('2023-05-09T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1, english=False), '05-09')

        d2 = fromiso('2023-11-01T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'November 1')

        d2 = fromiso('2023-11-01T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1, english=False), '11-01')

        d2 = fromiso('2024-05-09T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'May 9, 2024')

        d2 = fromiso('2024-05-09T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1, english=False), '2024-05-09')


class TestXOfYPages(unittest.TestCase):
    def test(self):
        self.assertEqual(xofypages(0, 5), 'none of 5 pages')
        self.assertEqual(xofypages(1, 5), '1 of 5 pages')
        self.assertEqual(xofypages(4, 5), '4 of 5 pages')
        self.assertEqual(xofypages(5, 5), 'all 5 pages')
        self.assertEqual(xofypages(0, 1), 'none of 1 page')
        self.assertEqual(xofypages(1, 1), 'all 1 page')


testnomap1 = '''key: value

Lines.
'''

testnomap2 = '''---

key: value
'''

test1 = '''---
key: value

Lines.
'''

test2 = '''---
key: value
---
Lines.
'''

test3 = '''---
key: val1  
long: this
    is more
    stuff
key: val2
---
Line.
Lines.
'''

class TestMetaFile(unittest.TestCase):
    def test(self):
        with io.StringIO(testnomap1) as fl: 
            body, map = MetaFile(None, stream=fl).read()
            self.assertEqual(body, testnomap1)
            self.assertEqual(map, {})
            
        with io.StringIO(testnomap2) as fl: 
            body, map = MetaFile(None, stream=fl).read()
            self.assertEqual(body, 'key: value\n')
            self.assertEqual(map, {})
            
        with io.StringIO(test1) as fl: 
            body, map = MetaFile(None, stream=fl).read()
            self.assertEqual(body, 'Lines.\n')
            self.assertEqual(map, { 'key':['value'] })

        with io.StringIO(test1) as fl:
            metafile = MetaFile(None, stream=fl)
            body, map = metafile.read()
            self.assertEqual(body, 'Lines.\n')
            self.assertEqual(map, { 'key':['value'] })
            body, map = metafile.read()
            self.assertEqual(body, 'Lines.\n')
            self.assertEqual(map, { 'key':['value'] })

        with io.StringIO(test2) as fl: 
            body, map = MetaFile(None, stream=fl).read()
            self.assertEqual(body, 'Lines.\n')
            self.assertEqual(map, { 'key':['value'] })

        with io.StringIO(test3) as fl: 
            body, map = MetaFile(None, stream=fl).read()
            self.assertEqual(body, 'Line.\nLines.\n')
            self.assertEqual(map, { 'key':['val1', 'val2'], 'long':['this', 'is more', 'stuff'] })

    def test_init(self):
        mf = MetaFile(init=( 'hello', { 'x':[1], 'y':[2,22] } ))
        body, map = mf.read()
        self.assertEqual(body, 'hello')
        self.assertEqual(map, { 'x':[1], 'y':[2,22] })


mtestex1 = '''Lines.
'''

mtestex2 = '''key: value

Lines.
'''

mtestnomap1 = '''---

key: value
'''

mtest1 = '''---
key: value

Lines.
'''

mtest2 = '''---
key: value

Lines.
---
'''

mtest3 = '''---
key: value

Lines.
----
'''

mtest4 = '''---
key: value

Lines.
----
---
'''

mtest5 = '''---
key: value
----
Lines.
----
'''

mtest6 = '''---
key: value
---
Lines.
----
'''

mtest7 = '''---
key: val1  
long: this
    is more
    stuff
key: val2
---
Line.
Lines.
---
foo: bar
-----
Test.
---
Other.
-----
'''


class TestMultiMetaFile(unittest.TestCase):
    def test(self):
        with io.StringIO(mtestex1) as fl:
            mmf = MultiMetaFile(None, stream=fl)
            self.assertRaises(Exception, mmf.read)
            
        with io.StringIO(mtestex2) as fl:
            mmf = MultiMetaFile(None, stream=fl)
            self.assertRaises(Exception, mmf.read)
            
        with io.StringIO(mtestnomap1) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('key: value\n', {}) ])
            
        with io.StringIO(mtest1) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])

        with io.StringIO(mtest1) as fl:
            metafile = MultiMetaFile(None, stream=fl)
            ls = metafile.read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])
            ls = metafile.read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])

        with io.StringIO(mtest2) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])

        with io.StringIO(mtest3) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('Lines.\n----\n', { 'key':['value'] }) ])

        with io.StringIO(mtest4) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('Lines.\n----\n', { 'key':['value'] }) ])

        with io.StringIO(mtest5) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])

        with io.StringIO(mtest6) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [ ('Lines.\n----\n', { 'key':['value'] }) ])

        with io.StringIO(mtest7) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            ls = [ mf.read() for mf in ls ]
            self.assertEqual(ls, [
                ('Line.\nLines.\n', { 'key':['val1', 'val2'], 'long':['this', 'is more', 'stuff'] }),
                ('Test.\n---\nOther.\n', { 'foo':['bar'] } ),
            ])


class TestAbsolutize(unittest.TestCase):
    def test(self):
        server = 'https://server/'

        self.assertEqual(absolutizeurls(
            '',
            serverurl=server),
            ''
        )
        self.assertEqual(absolutizeurls(
            'Plain text.\nWith line.\n',
            serverurl=server),
            'Plain text.\nWith line.\n'
        )
        self.assertEqual(absolutizeurls(
            'https://example.com/foo',
            serverurl=server),
            'https://example.com/foo'
        )
        self.assertEqual(absolutizeurls(
            '-<a href="https://example.com/foo">link</a>-',
            serverurl=server),
            '-<a href="https://example.com/foo">link</a>-'
        )
        self.assertEqual(absolutizeurls(
            '-<a href="/foo">link</a>-',
            serverurl=server),
            '-<a href="https://server/foo">link</a>-'
        )
        self.assertEqual(absolutizeurls(
            '-<a href="/foo">link</a>-<a href="/">link</a>-',
            serverurl=server),
            '-<a href="https://server/foo">link</a>-<a href="https://server/">link</a>-'
        )
        self.assertEqual(absolutizeurls(
            '<a rel="none" href="/foo">link</a>',
            serverurl=server),
            '<a rel="none" href="https://server/foo">link</a>'
        )
        self.assertEqual(absolutizeurls(
            '<a name="/foo">link</a>',
            serverurl=server),
            '<a name="/foo">link</a>'
        )
        self.assertEqual(absolutizeurls(
            '-<a href="/foo/bar">link</a>-<img src="/bar.png">-',
            serverurl=server),
            '-<a href="https://server/foo/bar">link</a>-<img src="https://server/bar.png">-'
        )
        self.assertEqual(absolutizeurls(
            '<img class="What" src="/bar.png" width="100">',
            serverurl=server),
            '<img class="What" src="https://server/bar.png" width="100">'
        )
        self.assertEqual(absolutizeurls(
            '<img href="/bar.png">',
            serverurl=server),
            '<img href="/bar.png">'
        )


class TestPageSet(unittest.TestCase):
    class MockPage:
        def __init__(self, outpath):
            self.outpath = outpath
        def __repr__(self):
            return '<MockPage "%s">' % (self.outpath,)
        
    def test(self):
        ps = PageSet()
        self.assertEqual(list(ps), [])
        self.assertEqual(len(ps), 0)
        
        pfoo = TestPageSet.MockPage('foo')
        pbar = TestPageSet.MockPage('bar')
        pfoobar = TestPageSet.MockPage('foo/bar')

        ps.add(pfoo)
        self.assertEqual(list(ps), [ pfoo ])
        
        ps.add(pfoo)
        self.assertEqual(list(ps), [ pfoo ])
        
        ps.add(pbar)
        self.assertEqual(list(ps), [ pfoo, pbar ])
        
        ps.add(pfoo)
        self.assertEqual(list(ps), [ pfoo, pbar ])
        
        ps.add(pfoobar)
        self.assertEqual(list(ps), [ pfoo, pbar, pfoobar ])
        self.assertEqual(len(ps), 3)

if __name__ == '__main__':
    unittest.main()
