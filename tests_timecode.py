from datetime import time
import unittest
from posttools.timecode import IncompatibleTimecode, InvalidTimecode, Timecode, TimecodeRange

class TestInstantiation(unittest.TestCase):
	
	def test_24_fromstring(self):
		tc = Timecode("01:00:00:00")
		self.assertIsInstance(tc, Timecode)
		self.assertEqual(tc.rate,24)
		self.assertEqual(tc.framenumber, 86400)
		self.assertEqual(str(tc), "01:00:00:00")
		self.assertEqual(tc.mode, Timecode.Mode.NDF)
	
	def test_30NDF_fromstring(self):
		tc = Timecode("01:00:00:00", 30)
		self.assertIsInstance(tc, Timecode)
		self.assertEqual(tc.rate,30)
		self.assertEqual(str(tc), "01:00:00:00")
		self.assertEqual(tc.framenumber, 108000)
	
	def test_30NDF_late_fromstring(self):
		tc = Timecode("22:15:08:13", 30)
		self.assertIsInstance(tc, Timecode)
		self.assertEqual(tc.rate,30)
		self.assertEqual(str(tc), "22:15:08:13")
	"""	
	def test_30DF_fromstring(self):
		tc = Timecode("01:00:00:00", 30, Timecode.Mode.DF)
		self.assertEqual(str(tc), "01:00:00;00")

	def test_30DF_late_fromstring(self):
		tc = Timecode("20:00:05;00", 30, Timecode.Mode.DF)
		self.assertEqual(str(tc), "20:00:05;00")
	"""
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

class TestTimecodeConversions(unittest.TestCase):

	def test_24_to_30(self):
		tc = Timecode("01:00:00:00")
		new_tc = tc.resample(rate=30)
		self.assertEqual(new_tc, Timecode("01:00:00:00", 30))
		self.assertEqual(new_tc.rate, 30)
		self.assertNotEqual(new_tc.framenumber, 86400)
		self.assertEqual(new_tc - 1, Timecode("59:59:29", 30))

		tc = Timecode("22:16:43:13")
		new_tc = tc.resample(rate=30)
		self.assertEqual(new_tc, Timecode("22:16:43:16", 30))

	def test_30_to_24(self):
		tc = Timecode("01:00:00:00", 30)
		new_tc = tc.resample(rate=24)
		self.assertEqual(new_tc, Timecode("01:00:00:00", 24))
		self.assertEqual(new_tc.framenumber, 86400)
		self.assertEqual(new_tc - 1, Timecode("59:59:23"))
	
	def test_30_to_30(self):
		tc = Timecode("01:00:00:00", 30)
		new_tc = tc.resample(rate=30)
		self.assertIs(tc, new_tc)	# Confirm passthrough

	def test_24_to_30DF(self):
		pass

	def test_30DF_to_30DF(self):
		pass

class TestTimecodeMath(unittest.TestCase):

	def test_add_number(self):
		self.assertEqual(Timecode("01:00:00:00") + 2, Timecode("01:00:00:02"))
		self.assertEqual(Timecode("23:12:14:22") - 20, Timecode("23:12:14:02"))
		self.assertEqual(Timecode("16:42:13:11", 30) + 31, Timecode("16:42:14:12", 30))
	
	def test_add_string(self):
		self.assertEqual(Timecode("01:00:00:00") + "02:25:16", Timecode("01:02:25:16"))
		self.assertEqual(Timecode("20:18:12:10", 30) + "1:1:1:1", Timecode("21:19:13:11", 30))
		self.assertEqual(Timecode("18:15", 15) - ":15", Timecode("00:00:18:00", 15))
		self.assertRaises(InvalidTimecode, lambda: Timecode("01:00:00:00") + "poop")
	
	def test_add_Timecode(self):
		self.assertEqual(Timecode("12:00:00:00") + Timecode("12:00:00:00"), Timecode("24:00:00:00"))
		self.assertEqual(Timecode("12:12:15:12") + Timecode("12:15:15",30), Timecode("12:24:31:00"))
		self.assertEqual(Timecode("12:12:15:15",30) + Timecode("12:15:12",24), Timecode("12:24:31:00",30))
	
	def test_equality(self):
		self.assertTrue(Timecode("12:12:12:12") == Timecode("12:12:12:12"))
		self.assertFalse(Timecode("12:12:12:12") == Timecode("12:12:12:13"))
		self.assertTrue(Timecode("12:12:12:12") != Timecode("12:12:12:12", 30))
		self.assertTrue(Timecode("12:12:12:12", 30) != Timecode("12:12:12:12", rate=30, mode=Timecode.Mode.DF))
		self.assertTrue(Timecode("01:00:00;00", rate=30, mode=Timecode.Mode.DF) == Timecode("01:00:00;00", rate=30, mode=Timecode.Mode.DF))
		self.assertTrue(Timecode("01:00:00:00") == 86400)
		self.assertTrue(Timecode("01:00:00;00", rate=30, mode=Timecode.Mode.DF) == 108000)	# TODO: Based on bad DF string to frame math. Will fail in future, and frankly, should.
	
	def test_cmp(self):
		self.assertTrue(Timecode("12:12:12:12") < Timecode("12:12:12:13"))
		self.assertTrue(Timecode("12:12:12:12") <= Timecode("12:12:12:13"))
		self.assertFalse(Timecode("12:12:12:12") > Timecode("12:12:12:13"))
		self.assertFalse(Timecode("12:12:12:12") >= Timecode("12:12:12:13"))

		self.assertTrue(Timecode("12:12:12:12") < Timecode("12:12:12:12", rate=30))
		self.assertTrue(Timecode("12:12:12:12") < Timecode("12:12:12:12", rate=30, mode=Timecode.Mode.DF))
		self.assertTrue(Timecode("12:12:12:12", rate=30) < Timecode("12:12:12:12", rate=30, mode=Timecode.Mode.DF))
	
	def test_sort(self):

		timecodes = [
			Timecode("12:00:00:00"),
			Timecode("11:00:00:13"), 
			Timecode("13:18:22:11", rate=30),
			Timecode("17:32:14;11", rate=30, mode=Timecode.Mode.DF),
			Timecode("314:31:24:14"),
			Timecode("13:18:22:11", rate=30),
			Timecode("17:32:14;11", rate=30, mode=Timecode.Mode.DF),
			Timecode("24:13:11:02", rate=15),
			Timecode("01:00:00;00", rate=30),
			Timecode("01:00:00:00", rate=30, mode=Timecode.Mode.DF)
		]

		timecodes_sorted = [
			Timecode("24:13:11:02", rate=15),
			Timecode("11:00:00:13"), 
			Timecode("12:00:00:00"),
			Timecode("314:31:24:14"),
			Timecode("01:00:00;00", rate=30),
			Timecode("13:18:22:11", rate=30),
			Timecode("13:18:22:11", rate=30),
			Timecode("01:00:00:00", rate=30, mode=Timecode.Mode.DF),
			Timecode("17:32:14;11", rate=30, mode=Timecode.Mode.DF),
			Timecode("17:32:14;11", rate=30, mode=Timecode.Mode.DF)
		]
		self.assertEqual(sorted(timecodes), timecodes_sorted)
		self.assertEqual(len(set(timecodes)), 8)

class TestTimecodeFormatting(unittest.TestCase):

	def test_24_onehour(self):
		tc = Timecode("01:00:00:00")
		self.assertEqual(str(tc), "01:00:00:00")
	
class TestTimecodeRange(unittest.TestCase):

	def test_range_duration(self):
		tr = TimecodeRange(
			start=Timecode("01:00:00:00", 24, Timecode.Mode.NDF),
			end=Timecode("01:01:00:00", 24, Timecode.Mode.NDF)
		)
		self.assertEqual(tr.duration.framenumber, Timecode("01:00:00", 24, Timecode.Mode.NDF).framenumber)
	
	def test_subrange_in_range(self):
		rate = 24
		mode = Timecode.Mode.NDF
		range_large = TimecodeRange(start=Timecode("01:00:00:00", rate, mode), end=Timecode("01:10:00:00", rate, mode))
		range_small = TimecodeRange(start=Timecode("01:00:10:00", rate, mode), end=Timecode("01:00:20:00", rate, mode))
		self.assertTrue(range_small in range_large)
		self.assertFalse(range_large in range_small)

	def test_range_in_range(self):
		rate = 24
		mode = Timecode.Mode.NDF
		range_large = TimecodeRange(start=Timecode("01:00:00:00", rate, mode), end=Timecode("01:10:00:00", rate, mode))
		self.assertTrue(range_large in range_large)
	
	def test_timecode_inplace_math(self):
		#rate = 24
		#mode = Timecode.Mode.NDF
		tc_base = Timecode("01:00:00:00")
		tc_base+=1
		self.assertEqual(tc_base, Timecode("01:00:00:01"))
	


if __name__ == "__main__":

	unittest.main()