import unittest
import datetime
import io

from util import tagfilename
from util import parsedate
from util import relativetime
from metafile import MetaFile
from metafile import MultiMetaFile

# Run me with:
#    python3 bloggor/testcase.py

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
            self.assertEqual(ls, [ ('key: value\n', {}) ])
            
        with io.StringIO(mtest1) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])

        with io.StringIO(mtest1) as fl:
            metafile = MultiMetaFile(None, stream=fl)
            ls = metafile.read()
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])
            ls = metafile.read()
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])

        with io.StringIO(mtest2) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])

        with io.StringIO(mtest3) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            self.assertEqual(ls, [ ('Lines.\n----\n', { 'key':['value'] }) ])

        with io.StringIO(mtest4) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            self.assertEqual(ls, [ ('Lines.\n----\n', { 'key':['value'] }) ])

        with io.StringIO(mtest5) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            self.assertEqual(ls, [ ('Lines.\n', { 'key':['value'] }) ])

        with io.StringIO(mtest6) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            self.assertEqual(ls, [ ('Lines.\n----\n', { 'key':['value'] }) ])

        with io.StringIO(mtest7) as fl: 
            ls = MultiMetaFile(None, stream=fl).read()
            self.assertEqual(ls, [
                ('Line.\nLines.\n', { 'key':['val1', 'val2'], 'long':['this', 'is more', 'stuff'] }),
                ('Test.\n---\nOther.\n', { 'foo':['bar'] } ),
            ])



if __name__ == '__main__':
    unittest.main()
