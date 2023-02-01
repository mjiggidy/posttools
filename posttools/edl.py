import enum, typing, io, re
from posttools.timecode import Timecode, TimecodeRange

class Fcm(enum.Enum):
	"""EDL frame counting modes"""
	# TODO: CMX3600: FCM does not appear in PAL systems
	NON_DROP_FRAME = "NON-DROP FRAME"
	DROP_FRAME = "DROP FRAME"

class _ParseModes(enum.Enum):
	START = enum.auto()
	TITLE = enum.auto()
	FCM   = enum.auto()
	EVENT_START = enum.auto()
	EVENT_DETAILS = enum.auto()

class Event:
	"""An EDL Event"""
	# CMX3600: Standard Form Statement
	pat_event = re.compile(r"^(?P<event_number>\d+)\s+(?P<reel_name>[^\s]+)\s+(?P<track_type>A\d*|B|V)\s+(?P<event_type>C|D|W\d+|K\s*[BO]?)\s+(?P<event_duration>\d*)\s+(?P<tc_src_in>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_src_out>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_rec_in>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_rec_out>\d{2}:\d{2}:\d{2}:\d{2})\s*$", re.I)

	"""
	TODO: CMX3600:
	F1: Event number. Decimal only.  If not decimal, considered note or note statement
	F2: Source. Three-digit reel number (001-253) followed by optional B.  Or BL (Black) or AX (Aux)
	F3: Channels involved A (Audio 1) B (Audio 1 and Video) V (Video) A2 (Audio 2) A2/V (Audio 2 and video) AA (Audio 1 and Audio 2) AA/V (A1/2 & Video)
	F4: Type of edit statement C (cut) D(dissolve), Wxxx (Wipe+CMX wipe code), KB (is the backround of a key), K (is key foreground), KO (is keyed out of the foreground)
	F5: Spaces if C.  001-255 if W, D, or K(?), "(F)" if KB with a fade condition
	F6: Source In
	F7: Source Out
	F8: Record In
	F9: Record Out (Reference only: CMX systems calculate this based on F6-8)

	"""

	def __init__(self, reel:str, track:"Track", source_tc:TimecodeRange, record_tc:TimecodeRange, fcm:Fcm):
		self._track = track
		self._fcm = fcm
		self._reel = reel
		self._tc_source = source_tc
		self._tc_record = record_tc
		self.notes = list() # TODO: Temp thing

		# TODO: CMX3600: BL (black) AX (aux) sources
		
	@property
	def track(self) -> "Track":
		"""The track this event belongs to"""
		return self._track
	
	@property
	def reel(self) -> str:
		return self._reel
	
	@property
	def tc_source(self) -> TimecodeRange:
		return self._tc_source
	
	@property
	def tc_record(self) -> TimecodeRange:
		return self._tc_record

	@property
	def fcm(self) -> Fcm:
		"""Frame counting mode of this event"""
		return self._fcm
	
	def __str__(self) -> str:
		notes = "\n".join(self.notes)
		return f"{self.reel} ({self.tc_record}):\n{notes}\n"

class Note:
	"""Note form statement"""

	""""
	TODO: CMX3600:
	FCM:	Frame code mode change (goes before event)
	SPLIT:	Audio/Video split in-time (goes before event) (?)
	GPI		GPI trigger
	M/S		Master/Slave
	SWM		Switcher memory
	M2		Motion memory
	%		Motion memory variable data

	Split examples: (TC is the delay relative to the in-point)
		SPLIT:    AUDIO DELAY=  00:00:00:05
		SPLIT:    VIDEO DELAY=  00:00:02:00
	"""
	

class Track:
	"""A track containing events in the EDL"""

	class Type(enum.Enum):
		"""Types of EDL tracks"""

		VIDEO = "V"
		"""Video track"""

		AUDIO = "A"
		"""Audio track"""

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




class Edl:
	"""An Edit Decision List"""

	"""
	TODO:
	Structurally, maybe Edl keeps a list of record TCs and references to Events that only track their local in/out
	"""
	
	def __init__(self, *, title:str="Untitled EDL", fcm:Fcm=Fcm.NON_DROP_FRAME, events:typing.Optional[typing.Iterable[Event]]=None):

		self.title = title
		self.fcm   = fcm
		self._events = list(events) if events else []

	@classmethod
	def from_file(cls, file_edl:io.BufferedReader):
		"""Create an EDL from an input file stream"""
		
		events = []

		event_buffer = []
		current_index = 0

		title = cls._parse_title(file_edl.readline())

		for line_num, line_edl in enumerate(l.rstrip('\n') for l in file_edl.readlines()):

			if not line_edl:
				continue

			try:
				# If starting next event, process event buffer and flush
				if event_buffer and cls._is_begin_new_event(line_edl, current_index):
					events.append(cls._parse_new_event_from_buffer(event_buffer))
					event_buffer=[]
					current_index = 0
				
				# Made note of our current event number if specified
				if line_edl.split()[0].isnumeric():
					current_index=int(line_edl.split()[0])
				
				event_buffer.append(line_edl)

			except Exception as e:
				raise ValueError(f"Line {line_num+2}: {e}")
		
		if event_buffer:
			events.append(cls._parse_new_event_from_buffer(event_buffer))
		
		return cls(title=title, fcm=Fcm.NON_DROP_FRAME, events=events)
	
	@staticmethod
	def _is_begin_new_event(line:str, current_index:int) -> bool:
		"""Determine if we're beginning a new event with this line"""

		if not current_index:
			return False

		first_token = line.split(maxsplit=1)[0]
		
		# Encountered prefixed form statement while parsing an event
		if first_token.lower() in ["FCM:","SPLIT:"]:
			return True
		
		# Encountered an event number different than the one we been doin'
		elif first_token.isnumeric() and int(first_token) != current_index:
			return True

		return False

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
	def _parse_new_event_from_buffer(buffer:typing.Iterable[str]) -> Event:
		"""Create a new event based on that match"""

		event = None
		notes = []
		for line in buffer:
			event_match = Event.pat_event.match(line)
			if event_match:
				event = Event(
					reel = event_match.group("reel_name"),
					source_tc = TimecodeRange(start=Timecode(event_match.group("tc_src_in")), end=Timecode(event_match.group("tc_src_out"))),
					record_tc = TimecodeRange(start=Timecode(event_match.group("tc_rec_in")), end=Timecode(event_match.group("tc_rec_out"))),
					track = Track(event_match.group("track_type")),
					fcm=Fcm.NON_DROP_FRAME #TODO: CHANGE THIS
				)

			else:
				notes.append(line)

		#print(source_tc, record_tc)

		if not event:
			raise ValueError("No event found")
		else:
			return event
	
	def write(self, file:io.TextIOBase):
		"""Write the EDL to a given stream"""

		print(f"TITLE: {self.title}", file=file)
		print(f"FCM: {self.fcm.value}", file=file)

		for event in self.events:
			print(event, file=file)

	@property
	def title(self) -> str:
		"""The title of the EDL"""
		#CMX3600: <=70 chars. Uppercase letters, spaces, numbers only
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
		if not isinstance(fcm, Fcm):
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