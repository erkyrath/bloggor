import unittest
import datetime

from util import tagfilename
from util import parsedate
from util import relativetime

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
        self.assertIsNone(relativetime(d2, d1))

        d2 = fromiso('2023-05-01T11:00:00+00:00')
        self.assertIsNone(relativetime(d2, d1))

        d2 = fromiso('2023-04-30T12:00:00+00:00')
        self.assertIsNone(relativetime(d2, d1))

        d2 = fromiso('2023-04-30T12:10:00+00:00')
        self.assertIsNone(relativetime(d2, d1))

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

        d2 = fromiso('2023-11-01T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'November 1')

        d2 = fromiso('2024-05-09T12:00:00+00:00')
        self.assertEqual(relativetime(d2, d1), 'May 9, 2024')


if __name__ == '__main__':
    unittest.main()
