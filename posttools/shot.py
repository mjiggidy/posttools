import timecode

class Metadata(dict):
	"""Shot metadata"""

class Shot:
	"""A shot"""
	name: str
	timecode: timecode.TimecodeRange
	metadata: Metadata