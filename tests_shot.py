import unittest
from posttools import shot, timecode

class TestMasterclip(unittest.TestCase):

	def test_shot_creation(self):
		sh = shot.Masterclip("A001C003_191003_R1CB", timecode.TimecodeRange(timecode.Timecode("01:00:00:00"), duration=timecode.Timecode(":01")), metadata=shot.Metadata({"Scene":"1","Take":"3","Camroll":"A001"}))
		self.assertEqual(sh.metadata.get("Camroll"), "A001")
		self.assertEqual(sh.timecode.start.framenumber, 86400)

	def test_shot_subclip(self):
		tc_master = timecode.TimecodeRange(
			timecode.Timecode("01:00:00:00"),
			timecode.Timecode("01:04:23:00")
		)
		meta = shot.Metadata({"Scene":"2A","Take":"1","Camroll":"A002"})

		sh = shot.Masterclip("A002C003_191003_R1CB", tc_master, meta)

		sub = shot.Subclip(sh, timecode.TimecodeRange(
			timecode.Timecode("01:00:00:00"),
			timecode.Timecode("01:04:23:00")
			)
		)

		self.assertIsInstance(sub, shot.Subclip)
		self.assertEqual(sub.metadata.get("Camroll"), sh.metadata.get("Camroll"))
		print(sub.timecode)

if __name__ == "__main__":
	unittest.main()