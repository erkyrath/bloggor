import unittest

from util import parsedate
from util import tagfilename

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
        self.assertIsNone(parsedate(None))
        self.assertIsNone(parsedate(''))
        self.assertIsNone(parsedate('2023-05-1'))
        self.assertIsNone(parsedate('2023-5-01'))
        self.assertIsNone(parsedate('2023-05-01T12:00:00-00:00'))
        self.assertIsNone(parsedate('2023-05-01T12:00:00+05:00'))
        self.assertIsNone(parsedate('2023-05-01 12:00:00+00:00'))

if __name__ == '__main__':
    unittest.main()
