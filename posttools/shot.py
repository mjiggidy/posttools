import typing, abc, enum
from .timecode import TimecodeRange, Timecode

class IncompatibleTrack(Exception):
	"""A given track is not compatible with the shot"""

class Metadata(dict):
	"""Shot metadata"""

class Track(abc.ABC):
	"""An individual track belonging to a shot"""

class VideoTrack(Track):
	"""A video track"""
	frame_rate:float

class AudioTrack(Track):
	"""An audio track"""	
	sampling_rate:float

class AbstractDataTrack(Track, abc.ABC):
	"""Do your own thang"""

	@abc.abstractmethod
	def data_at_timecode(self, timecode:Timecode) -> typing.Any:
		"""Return data for a given timecode in the shot""" 

class Shot(abc.ABC):
	"""Abtract class for shots"""

	@abc.abstractmethod
	def name(self) -> str:
		"""Tape or reel name"""
	
	@abc.abstractmethod
	def metadata(self) -> Metadata:
		"""Metadata for shot"""

	@abc.abstractmethod
	def timecode(self) -> TimecodeRange:
		"""Timecode of shot"""
	
	@abc.abstractmethod
	def subclip(self, timecode:TimecodeRange) -> "Subclip":
		"""Create a subclip of this shot"""
	
	def __eq__(self, other) -> bool:
		return self.name == other.name and self.timecode == other.timecode
	
	def __lt__(self, other) -> bool:
		if self.name < other.name:
			return True
		elif self.name == other.name and self.timecode < other.timecode:
			return True
		else:
			return False
	
	# TODO: Gotta test this
	def __gt__(self, other) -> bool:
		return all([not self < other, self != other])
	
	def __contains__(self, other) -> bool:
		if not isinstance(other, Shot): return False
		return self.name == other.name and other.timecode in self.timecode



class Masterclip(Shot):
	"""A clip of original source material"""

	def __init__(self, name:str, timecode:TimecodeRange, metadata:typing.Optional[Metadata]=None):
		"""A clip of original source material"""

		self._name = name
		self._timecode = timecode
		self._tracks = []

		if metadata is None:
			self._metadata = Metadata()
		elif isinstance(metadata, Metadata):
			self._metadata = metadata
		else:
			raise ValueError("Metadata must be an instance of the Metadata class")
	
	@property
	def name(self) -> str:
		"""Tape/reel name"""
		return self._name
	
	@property
	def timecode(self) -> TimecodeRange:
		"""Timecode range"""
		return self._timecode

	@property
	def metadata(self) -> Metadata:
		"""Shot metadata"""
		return self._metadata
	
	def addVideoTrack(self, track:VideoTrack):
		"""Add a video track to the shot"""
		if round(track.frame_rate) != self.timecode.rate:
			raise IncompatibleTrack(f"The video track frame rate ({track.frame_rate}) is incompatible with this shot's timecode format ({self.timecode.rate} {self.timecode.mode})")
	
	def subclip(self, timecode:TimecodeRange) -> "Subclip":
		"""Make a subclip from this masterclip"""
		return Subclip(self, timecode)

	def __repr__(self) -> str:
		return f"<{self._name} {self._timecode.start}-{self._timecode.end}>"

class Subclip(Shot):
	"""Subclip of a masterclip"""

	def __init__(self, masterclip:Shot, timecode:TimecodeRange):
		"""A subset of another masterclip or subclip"""
		
		# TODO: Maybe it's ok to just subclip a subclip and make its parent be a subclip
		# Could do separate methods for "parent" clip as well as access to the ultimate "master" clip
		# I don't know, man
		
		if isinstance(masterclip, self.__class__):
			self._master = masterclip.masterclip
		else:
			self._master = masterclip
		
		if timecode not in masterclip.timecode:
			raise ValueError(f"Subclipped timecode ({timecode.start}-{timecode.end}) exceeds the bounds of the masterclip ({masterclip.timecode.start}-{masterclip.timecode.end})")
		
		self._timecode = timecode
	
	@property
	def timecode(self) -> TimecodeRange:
		return self._timecode
	
	@property
	def metadata(self) -> Metadata:
		return self._master.metadata
	
	@property
	def name(self) -> str:
		return self._master.name
	
	@property
	def masterclip(self) -> Masterclip:
		return self._master
	
	def subclip(self, timecode:TimecodeRange) -> "Subclip":
		"""Make a subclip from this masterclip"""
		return Subclip(self._master, timecode)
	
	def __repr__(self) -> str:
		return f"<Subclip of {self._master.name}, {self.timecode}>"