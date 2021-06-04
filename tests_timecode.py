from datetime import time
import unittest
from posttools.timecode import Timecode, TimecodeRange

class TestInstantiation(unittest.TestCase):
	
	def test_24_fromstring(self):
		tc = Timecode("01:00:00:00")
		self.assertIsInstance(tc, Timecode)
		self.assertEqual(tc.rate,24)
		self.assertEqual(tc.framenumber, 86400)
		self.assertEqual(str(tc), "01:00:00:00")
		self.assertEqual(tc.mode, Timecode.Mode.NDF)
	
	def test_30_fromstring(self):
		tc = Timecode("01:00:00:00", 30)
		self.assertIsInstance(tc, Timecode)
		self.assertEqual(tc.rate,30)
		self.assertEqual(str(tc), "01:00:00:00")
		self.assertEqual(tc.framenumber, 108000)

	def test_24_fromint(self):
		tc = Timecode(86400)
		self.assertIsInstance(tc, Timecode)
		self.assertEqual(tc.rate,24)
		self.assertEqual(tc.framenumber, 86400)
		self.assertEqual(str(tc), "01:00:00:00")
		self.assertEqual(tc.mode, Timecode.Mode.NDF)

	def test_24_fromnegint(self):
		tc = Timecode(-86400)
		self.assertIsInstance(tc, Timecode)
		self.assertEqual(tc.rate,24)
		self.assertEqual(tc.framenumber, -86400)
		self.assertEqual(str(tc), "-01:00:00:00")
		self.assertEqual(tc.mode, Timecode.Mode.NDF)
		self.assertEqual(tc.hours, -1)
	
	def test_lt_true(self):
		rate = 24
		mode = Timecode.Mode.NDF
		self.assertTrue(Timecode("01:00:00:00", rate, mode) < Timecode("01:00:10:00", rate, mode))
	
class TestTimecodeRange(unittest.TestCase):

	def test_range_duration(self):
		tr = TimecodeRange(
			Timecode("01:00:00:00", 24, Timecode.Mode.NDF),
			Timecode("01:01:00:00", 24, Timecode.Mode.NDF)
		)
		self.assertEqual(tr.duration.framenumber, Timecode("01:00:00", 24, Timecode.Mode.NDF).framenumber)
	
	def test_subrange_in_range(self):
		rate = 24
		mode = Timecode.Mode.NDF
		range_large = TimecodeRange(Timecode("01:00:00:00", rate, mode), Timecode("01:10:00:00", rate, mode))
		range_small = TimecodeRange(Timecode("01:00:10:00", rate, mode), Timecode("01:00:20:00", rate, mode))
		self.assertTrue(range_small in range_large)
		self.assertFalse(range_large in range_small)

	def test_range_in_range(self):
		rate = 24
		mode = Timecode.Mode.NDF
		range_large = TimecodeRange(Timecode("01:00:00:00", rate, mode), Timecode("01:10:00:00", rate, mode))
		self.assertTrue(range_large in range_large)
	


if __name__ == "__main__":

	unittest.main()