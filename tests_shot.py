import unittest
from posttools import shot, timecode

class TestMasterclip(unittest.TestCase):

	def test_shot_creation(self):
		sh = shot.Masterclip("A001C003_191003_R1CB", timecode.TimecodeRange(timecode.Timecode("01:00:00:00"), duration=timecode.Timecode(":01")), metadata=shot.Metadata({"Scene":"1","Take":"3","Camroll":"A001"}))
		self.assertEqual(sh.metadata.get("Camroll"), "A001")
		self.assertEqual(sh.timecode.start.framenumber, 86400)

if __name__ == "__main__":
	unittest.main()