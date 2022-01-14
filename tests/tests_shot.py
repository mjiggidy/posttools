import unittest
from posttools.shot import Masterclip, Subclip, Metadata
from posttools.timecode import Timecode, TimecodeRange

class TestMasterclip(unittest.TestCase):

	def test_shot_creation(self):
		sh = Masterclip("A001C003_191003_R1CB", TimecodeRange(Timecode("01:00:00:00"), duration=Timecode(":01")), metadata=Metadata({"Scene":"1","Take":"3","Camroll":"A001"}))
		self.assertEqual(sh.metadata.get("Camroll"), "A001")
		self.assertEqual(sh.timecode.start.framenumber, 86400)

	def test_shot_subclip(self):
		tc_master = TimecodeRange(
			Timecode("01:00:00:00"),
			Timecode("01:04:23:00")
		)
		meta = Metadata({"Scene":"2A","Take":"1","Camroll":"A002"})

		sh = Masterclip("A002C003_191003_R1CB", tc_master, meta)

		sub = Subclip(sh, TimecodeRange(
			Timecode("01:00:00:00"),
			Timecode("01:04:23:00")
			)
		)

		self.assertIsInstance(sub, Subclip)
		self.assertEqual(sub.metadata.get("Camroll"), sh.metadata.get("Camroll"))
	
class TestSubclip(unittest.TestCase):

	def test_create_subclip(self):
		rate = 24
		mode = Timecode.Mode.NDF
		full_range = TimecodeRange(
			Timecode("01:00:00:00", rate, mode),
			duration = Timecode("05:00:00", rate, mode)
		)

		master = Masterclip("A001C003_211003_R1CB", full_range)
		master.metadata.update({"Camroll":"A001"})

		sub = master.subclip(
			TimecodeRange(
				Timecode("01:00:02:23", rate, mode),
				duration = Timecode("03:00", rate, mode)
			)
		)

		self.assertEqual(sub.metadata.get("Camroll"), master.metadata.get("Camroll"))
		self.assertTrue(sub.timecode in master.timecode)
		self.assertTrue(sub in master)
		self.assertFalse(master in sub)
		self.assertTrue(sub in sub)
		
		subsub = sub.subclip(TimecodeRange(
			Timecode("01:00:03:00", rate, mode),
			duration = Timecode("02", rate, mode)
		))

		self.assertTrue(subsub in master)
		print(subsub)

if __name__ == "__main__":
	unittest.main()