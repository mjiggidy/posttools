import enum, typing, io, re
from posttools.timecode import Timecode, TimecodeRange

class Event:
	"""An EDL Event"""
	pat_event = re.compile(r"^(?P<event_number>\d+)\s+(?P<reel_name>[^\s]+)\s+(?P<track_type>A\d*|B|V)\s+(?P<event_type>C|D|W\d+|K\s*[BO]?)\s+(?P<event_duration>\d*)\s+(?P<tc_src_in>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_src_out>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_rec_in>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_rec_out>\d{2}:\d{2}:\d{2}:\d{2})\s*$", re.I)

	def __init__(self, reel:str, track:"Track", source_tc:TimecodeRange, record_tc:TimecodeRange):
		self._track = track
		self.reel = reel
		
	@property
	def track(self) -> "Track":
		"""The track this event belongs to"""
		return self._track

class Track:
	"""A track containing events in the EDL"""

	class Type(enum.Enum):
		"""Types of EDL tracks"""

		VIDEO = "V"
		"""Video track"""

		AUDIO = "A"
		"""Audio track"""

		BLACK = "B"
		"""Black"""

	def __init__(self, name:str):
		"""Create a new EDL track"""

		self._type = self.__class__.Type(name[0].upper())
		self._index = int(name[1:]) if len(name) > 1 else 1
	
	@property
	def name(self) -> str:
		"""The name of the track"""
		if self._index > 1:
			return self._type.value + str(self._index)
		else:
			return self._type.value
	
	@property
	def type(self) -> Type:
		"""The type of data in this EDL track"""
		return self._type
	
	def __eq__(self, other) -> bool:
		if not isinstance(other, self.__class__):
			return False
		return self.name == other.name
	
	def __hash__(self) -> int:
		return hash(self.name)
	
	def __str__(self) -> str:
		return self.name
	
	def __repr__(self) -> str:
		return f"<{self.__class__.__name__} name={self.name}>"



class Fcm(enum.Enum):
	"""EDL frame counting modes"""
	NON_DROP_FRAME = "NON-DROP FRAME"
	DROP_FRAME = "DROP FRAME"

class _ParseModes(enum.Enum):
	START = enum.auto()
	TITLE = enum.auto()
	FCM   = enum.auto()
	EVENT_START = enum.auto()
	EVENT_DETAILS = enum.auto()

class Edl:
	"""An Edit Decision List"""
	
	def __init__(self, *, title:str="Untitled EDL", fcm:Fcm=Fcm.NON_DROP_FRAME, events:typing.Optional[typing.Iterable[Event]]=None):

		self._title = title
		self._fcm   = fcm
		self._events = list(events) if events else []

	@classmethod
	def from_file(cls, file:io.BufferedReader):
		"""Create an EDL from an input file stream"""

		mode =_ParseModes.TITLE
		events = list()

		for line_num, line_edl in enumerate(l.rstrip('\n') for l in file.readlines()):


			try:
				if mode == _ParseModes.TITLE:
					# Get the EDL title
					title = cls._parse_title(line_edl)
					mode = _ParseModes.FCM

				elif mode == _ParseModes.FCM:
					# Get the Frame Count Mode
					fcm = cls._parse_fcm(line_edl)
					mode = _ParseModes.EVENT_START
				
				elif mode == _ParseModes.EVENT_START:
					# Parse events
					event_match = Event.pat_event.match(line_edl)
					if event_match:
						event = cls._parse_new_event(event_match)
						events.append(event)

				
			except Exception as e:
				raise ValueError(f"Line {line_num+1}: {e}")
		
		return cls(title=title, fcm=fcm, events=events)
			
	@staticmethod
	def _parse_title(line:str) -> str:
		"""Extract a title from a line in an EDL"""
		start = "title:"
		if not line.lower().startswith(start):
			raise ValueError("Title was expected, but not found")
		title = line[len(start):].strip()
		if not len(title):
			raise ValueError("Title is empty")
		return title
	
	@staticmethod
	def _parse_fcm(line:str) -> Fcm:
		"""Extract the FCM from a line in an EDL"""
		start = "fcm:"
		if not line.lower().startswith(start):
			raise ValueError("FCM was expected, but not found")
		try:
			fcm = Fcm(line[len(start):].strip())
		except:
			raise ValueError("Invalid FCM specified")
		return fcm
	
	# TODO: Maybe these parsers belong in the class they are related to.
	# That mades TOO much sense.
	@staticmethod
	def _parse_new_event(event_match:re.Match) -> Event:
		"""Create a new event based on that match"""
		track = Track(event_match.group("track_type"))
		source_tc = TimecodeRange(start=Timecode(event_match.group("tc_src_in")), end=Timecode(event_match.group("tc_src_out")))
		record_tc = TimecodeRange(start=Timecode(event_match.group("tc_rec_in")), end=Timecode(event_match.group("tc_rec_out")))

		print(source_tc, record_tc)


		return Event(reel=event_match.group("reel_name"), source_tc=source_tc, record_tc=record_tc, track=track)
	
	def write(self, file:io.TextIOBase):
		"""Write the EDL to a given stream"""

		print(f"TITLE: {self.title}", file=file)
		print(f"FCM: {self.fcm.value}", file=file)

#		for event in self.events:
#			print(event, file=file)

	@property
	def title(self) -> str:
		"""The title of the EDL"""
		return self._title
	
	@title.setter
	def title(self, title:str):
		"""Validate and set the EDL title"""
		
		title = str(title).strip()
		
		if not len(title):
			raise ValueError(f"The title cannot be an empty string")
		
		if len(title.splitlines()) > 1:
			raise ValueError(f"The title must not contain line breaks")
		
		self._title = title

	@property
	def fcm(self) -> Fcm:
		"""The frame counting mode for this EDL"""
		return self._fcm
	
	@fcm.setter
	def fcm(self, fcm:Fcm):
		if not isinstance(fcm, self.Fcm):
			raise ValueError("Invalid FCM provided")
		self._fcm = fcm
	
	@property
	def tracks(self) -> list[Track]:
		"""The tracks used in this EDL"""
		return set(event.track for event in self.events)
	
	@property
	def events(self) -> list[Event]:
		"""An EDL event"""
		return self._events
	
	def __str__(self):
		file_text = io.StringIO()
		self.write(file_text)
		return file_text.getvalue()
	
	def __repr__(self):
		return f"<{self.__class__.__name__} title={self.title} FCM={self.fcm} events={len(self.events)}>"