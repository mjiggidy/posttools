import unittest
from posttools import timecode

class TestInstantiation(unittest.TestCase):
	
	def test_24_fromstring(self):
		tc = timecode.Timecode("01:00:00:00")
		self.assertIsInstance(tc, timecode.Timecode)
		self.assertEqual(tc.rate,24)
		self.assertEqual(tc.framenumber, 86400)
		self.assertEqual(str(tc), "01:00:00:00")
		self.assertEqual(tc.mode, timecode.Timecode.Mode.NDF)
	
	def test_30_fromstring(self):
		tc = timecode.Timecode("01:00:00:00", 30)
		self.assertIsInstance(tc, timecode.Timecode)
		self.assertEqual(tc.rate,30)
		self.assertEqual(str(tc), "01:00:00:00")
		self.assertEqual(tc.framenumber, 108000)

	def test_24_fromint(self):
		tc = timecode.Timecode(86400)
		self.assertIsInstance(tc, timecode.Timecode)
		self.assertEqual(tc.rate,24)
		self.assertEqual(tc.framenumber, 86400)
		self.assertEqual(str(tc), "01:00:00:00")
		self.assertEqual(tc.mode, timecode.Timecode.Mode.NDF)

	def test_24_fromnegint(self):
		tc = timecode.Timecode(-86400)
		self.assertIsInstance(tc, timecode.Timecode)
		self.assertEqual(tc.rate,24)
		self.assertEqual(tc.framenumber, -86400)
		self.assertEqual(str(tc), "-01:00:00:00")
		self.assertEqual(tc.mode, timecode.Timecode.Mode.NDF)
		self.assertEqual(tc.hours, -1)


if __name__ == "__main__":

	unittest.main()