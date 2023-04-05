import enum, typing, io, re, functools, abc
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

class SourceReel(abc.ABC):
	"""A base source for use as a reel name in a Standard Form Statement"""

	@property
	def _NAME(self) -> str:
		pass

	@property
	def name(self) -> str:
		"""The reel name"""
		return self._NAME
	
	def __str__(self):
		return self.name
	
	def __eq__(self, other):
		return self._NAME == other._NAME
	
	def __hash__(self):
		return hash(self._NAME)
	
	@classmethod
	def from_string(cls, reel_name:str):

		if BlackSource.validate(reel_name):
			return BlackSource
		elif AuxSource.validate(reel_name):
			return AuxSource
		elif TapeSource.validate(reel_name):
			return TapeSource(reel_name)
		else:
			raise ValueError("Reel name format is not recognized")

class BlackSource(SourceReel):
	"""A black/empty source"""

	_NAME = "BL"

	@classmethod
	def validate(self, reel_name:str) -> bool:
		"""Is this a valid Black source"""
		return reel_name.upper() == "BL"

class AuxSource(SourceReel):
	"""An auxillary source"""

	_NAME = "AX"

	@classmethod
	def validate(self, reel_name:str) -> bool:
		return reel_name.upper() == "AX"

class TapeSource(SourceReel):

	_NAME = str()

	def __init__(self, reel_name:str):

		if not self.validate(reel_name):
			raise ValueError(f"Reel name contains invalid characters for this source type")

		super().__init__()
		self._NAME = reel_name

	@classmethod
	def validate(cls, reel_name:str) -> bool:
		return len(reel_name.strip()) and not re.search("\s", reel_name)


class StandardFormStatement(abc.ABC):
	"""A base standard form statement"""

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

	def __init__(self, reel_name:str, tracks:typing.Iterable["Track"], timecode_source:TimecodeRange, timecode_record:TimecodeRange, event_number:typing.Optional[int]=None):
		"""Basic parsing of common elements"""
		self._reel = SourceReel.from_string(reel_name)
		self._tracks = tracks
		self._timecode_source = timecode_source
		self._timecode_record = timecode_record
		self._event_number = int(event_number) if event_number is not None else None

	@classmethod
	def all_statement_types(cls) -> typing.Generator["StandardFormStatement", None, None]:
		"""Return all subclasses of this type of statement"""

		for statement in cls.__subclasses__():
			yield from statement.all_statement_types()
			yield statement
	
	@property
	def PAT_EVENT(self) -> re.Pattern:
		"""Regex pattern matching this statement type"""
		pass

	@abc.abstractclassmethod
	def parse_from_pattern(self, statement:re.Pattern) -> "StandardFormStatement":
		"""Create a statement object from a parsed regex object"""
		pass

	@classmethod
	def parse_from_string(cls, line:str) -> "StandardFormStatement":
		"""Create a statement object from a given line from an EDL"""
		pat = cls.PAT_EVENT.match(line)
		if not pat:
			raise ValueError(f"This line is not a valid {cls.__name__}")
		return cls.parse_from_pattern(pat)
	
	@classmethod
	def _parse_shared_elements(cls, statement:re.Pattern) -> typing.Tuple[int, str, typing.Set["Track"], TimecodeRange, TimecodeRange]:

		event_number = int(statement.group("event_number"))
		reel_name = statement.group("reel_name")
		tracks = {Track(statement.group("track_type"))}
		timecode_source = TimecodeRange(
			start=Timecode(statement.group("tc_src_in")), end=Timecode(statement.group("tc_src_out"))
		)
		timecode_record = TimecodeRange(
			start=Timecode(statement.group("tc_rec_in")), end=Timecode(statement.group("tc_rec_out"))
		)

		return event_number, reel_name, tracks, timecode_source, timecode_record
	
	@property
	def source(self) -> SourceReel:
		"""The source reel referenced for this statement"""
		return self._reel

	@property
	def reel_name(self) -> str:
		"""The reel name referenced for this statement"""
		return str(self.source._NAME)
	
	@property
	def tracks(self) -> typing.Set["Track"]:
		"""The tracks referenced in this statement"""
		return self._tracks
	
	@property
	def timecode_source(self) -> TimecodeRange:
		"""The timecode range used by the source reel"""
		return self._timecode_source
	
	@property
	def timecode_record(self) -> TimecodeRange:
		"""The timecode range the source appears in the timeline"""
		return self._timecode_record
	
	@property
	def event_number(self) -> typing.Union[int,None]:
		"""The original event number from the originating EDL"""
		return self._event_number
	
	@property
	def fcm(self) -> "Fcm":
		"""The Frame Counting Mode for this statement"""
		# TODO: No hardcode no mo plz bb
		return Fcm.NON_DROP_FRAME

class CutStatement(StandardFormStatement):
	"""A simple cut"""

	def __init__(self, reel_name:str, tracks:typing.Iterable["Track"], timecode_source:TimecodeRange, timecode_record:TimecodeRange, event_number:typing.Optional[int]=None):

		super().__init__(
			reel_name=reel_name,
			timecode_source=timecode_source,
			timecode_record=timecode_record,
			tracks=tracks,
			event_number=event_number
		)

	PAT_EVENT = re.compile(
		r"^(?P<event_number>\d+)\s+"
		r"(?P<reel_name>[^\s]+)\s+"
		r"(?P<track_type>A\d*|B|V)\s+"
		r"(?P<event_type>C)\s+"
		r"(?P<tc_src_in>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_src_out>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_rec_in>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_rec_out>\d{2}:\d{2}:\d{2}:\d{2})\s*$"
	, re.I)

	@classmethod
	def parse_from_pattern(cls, statement:re.Pattern) -> "CutStatement":
		"""Create a Cut Statement from a parsed regex string"""

		event_number, reel_name, tracks, timecode_source, timecode_record = super()._parse_shared_elements(statement)

		return cls(
			reel_name = reel_name,
			tracks = tracks,
			timecode_source = timecode_source,
			timecode_record = timecode_record,
			event_number = event_number
		)
	
	def __str__(self):
		# TODO: Additional formatting options (spacing, number padding)
		return f"{str(self.event_number if self.event_number is not None else 1).zfill(3)}  {self.reel_name.ljust(128)}  {str().join(t.name for t in self.tracks).ljust(3)}  C       {self.timecode_source.start} {self.timecode_source.end} {self.timecode_record.start} {self.timecode_record.end}"

class DissolveStatement(StandardFormStatement):
	"""A dissolve statement"""

	PAT_EVENT = re.compile(
		r"^(?P<event_number>\d+)\s+"
		r"(?P<reel_name>[^\s]+)\s+"
		r"(?P<track_type>A\d*|B|V)\s+"
		r"(?P<event_type>D)\s+"
		r"(?P<event_duration>\d+)\s+"
		r"(?P<tc_src_in>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_src_out>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_rec_in>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_rec_out>\d{2}:\d{2}:\d{2}:\d{2})\s*$"
	, re.I)

	def __init__(self, reel_name:str, tracks:typing.Iterable["Track"], timecode_source:TimecodeRange, timecode_record:TimecodeRange, dissolve_length:int, event_number:typing.Optional[int]=None):

		super().__init__(
			reel_name=reel_name,
			timecode_source=timecode_source,
			timecode_record=timecode_record,
			tracks=tracks,
			event_number=event_number
		)

		self._dissolve_length = int(dissolve_length)
	
	@property
	def dissolve_length(self) -> int:
		"""Length in frames of the dissolve"""
		return self._dissolve_length

	@classmethod
	def parse_from_pattern(cls, statement:re.Pattern) -> "DissolveStatement":
		"""Create a Dissolve Statement from a parsed regex string"""

		event_number, reel_name, tracks, timecode_source, timecode_record = super()._parse_shared_elements(statement)

		return cls(
			reel_name = reel_name,
			tracks = tracks,
			dissolve_length = int(statement.group("event_duration")),
			timecode_source = timecode_source,
			timecode_record = timecode_record,
			event_number = event_number
		)

	def __str__(self):
		# TODO: Additional formatting options
		return f"{str(self.event_number if self.event_number is not None else 1).zfill(3)}  {self.reel_name.ljust(128)}  {str().join(t.name for t in self.tracks).ljust(3)}  D  {str(self.dissolve_length).zfill(3)}  {self.timecode_source.start} {self.timecode_source.end} {self.timecode_record.start} {self.timecode_record.end}"

class WipeStatement(StandardFormStatement):
	"""A wipe statement"""

	PAT_EVENT = re.compile(
		r"^(?P<event_number>\d+)\s+"
		r"(?P<reel_name>[^\s]+)\s+"
		r"(?P<track_type>A\d*|B|V)\s+"
		r"(?P<event_type>W\d+)\s+"
		r"(?P<event_duration>\d+)\s+"
		r"(?P<tc_src_in>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_src_out>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_rec_in>\d{2}:\d{2}:\d{2}:\d{2})\s+"
		r"(?P<tc_rec_out>\d{2}:\d{2}:\d{2}:\d{2})\s*$"
	, re.I)

	def __init__(self, reel_name:str, tracks:typing.Iterable["Track"], timecode_source:TimecodeRange, timecode_record:TimecodeRange, wipe_length:int, wipe_id:int, event_number:typing.Optional[int]=None):

		super().__init__(
			reel_name=reel_name,
			timecode_source=timecode_source,
			timecode_record=timecode_record,
			tracks=tracks,
			event_number=event_number
		)

		self._wipe_length = int(wipe_length)
		self._wipe_id     = int(wipe_id)

	@classmethod
	def parse_from_pattern(cls, statement:re.Pattern) -> "WipeStatement":
		"""Create a Dissolve Statement from a parsed regex string"""

		event_number, reel_name, tracks, timecode_source, timecode_record = super()._parse_shared_elements(statement)

		return cls(
			reel_name = reel_name,
			tracks = tracks,
			wipe_length = int(statement.group("event_duration")),
			wipe_id     = int(statement.group("event_type")[1:]),
			timecode_source = timecode_source,
			timecode_record = timecode_record,
			event_number = event_number
		)
	
	@property
	def wipe_length(self) -> int:
		"""Length in frames of the wipe"""
		return self._wipe_length
	
	@property
	def wipe_id(self) -> int:
		"""CMX Wipe ID"""
		return self._wipe_id
	
	def __str__(self):
		# TODO: Additional formatting options
		return f"{str(self.event_number if self.event_number is not None else 1).zfill(3)}  {self.reel_name.ljust(128)}  {str().join(t.name for t in self.tracks).ljust(3)}  W{str(self.wipe_id).zfill(3)}  {str(self.wipe_length).zfill(3)}  {self.timecode_source.start} {self.timecode_source.end} {self.timecode_record.start} {self.timecode_record.end}"

class NoteFormStatement(abc.ABC):
	pass

class Event:
	"""An EDL Event"""

	def __init__(self, standard_statements:typing.Iterable[StandardFormStatement], note_statements:typing.Optional[typing.Iterable["NoteFormStatement"]]=None, comments=typing.Optional[typing.Iterable[str]]):

		self._sfs = list(standard_statements)
		self._nfs = note_statements if note_statements else []
		
		fcm = {s.fcm for s in self._sfs}
		if len(fcm) != 1:
			raise ValueError(f"Standard Form Statements must have matching FCMs")
		self._fcm = fcm.pop()

		self.comments = comments if comments else list() # TODO: Temp thing

	@classmethod
	def from_string(cls, event:str) -> "Event":
		"""Parse an event from an event string"""

		sfs = list()
		nfs = list()
		comments = list()

		for line in event.splitlines(keepends=False):
			if not line.strip():
				continue

			parsed = cls._identify_line(line)
			if isinstance(parsed, StandardFormStatement):
				sfs.append(parsed)
			elif isinstance(parsed, str):
				comments.append(parsed)
			else:
				raise ValueError(f"Unrecognized line (of type {type(parsed)})in event: {line}")
		
		return cls(
			standard_statements = sfs,
			note_statements = nfs,
			comments = comments
		)
			
	@classmethod
	def _identify_line(cls, line:str) -> typing.Union[re.Pattern, str, None]:
		"""Identify a line"""
		for s in StandardFormStatement.all_statement_types():
			match = s.PAT_EVENT.match(line)
			if match:
				parsed = s.parse_from_pattern(match)
				return parsed
		return line
		
	@property
	def tracks(self) -> typing.Set["Track"]:
		"""The track(s) this event belongs to"""
		tracks = set()
		for s in self._sfs:
			for track in s.tracks:
				tracks.add(track)
		return tracks
	
	@property
	def sources(self) -> typing.Set[SourceReel]:
		return set(s.source for s in self._sfs)
	
	@property
	def reel_names(self) -> typing.Set[str]:
		return set(s.reel_name for s in self._sfs)
	
	@property
	def timecode_extents(self) -> TimecodeRange:
		"""The full extents of this event"""
		return TimecodeRange(
			start = min(s.timecode_record.start for s in self._sfs),
			end   = max(s.timecode_record.end for s in self._sfs)
		)
	
	@property
	def duration(self) -> Timecode:
		"""The duraction of this event"""
		return self.timecode_extents.duration
	
	@property
	def fcm(self) -> Fcm:
		"""Frame counting mode of this event"""
		return self._fcm
	
	def __str__(self) -> str:
		# TODO: Add the rest
		output = str()
		output += "\n".join(str(s) for s in self._sfs)

		output += "\n"

		output += "\n".join(str(n) for n in self._nfs)

		output += "\n"

		output += "\n".join(str(c) for c in self.comments)

		return output

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
	
@functools.total_ordering
class Track:
	"""A track containing events in the EDL"""

	tracks = set()

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
		
	@property
	def track_index(self) -> int:
		"""The track index for the given track type"""
		return self._index
	
	def __eq__(self, other) -> bool:
		if not isinstance(other, self.__class__):
			return False
		return self.name == other.name
	
	def __lt__(self, other) -> bool:
		if not isinstance(other, self.__class__):
			return False
		return self.track_index < other.track_index
	
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

		title = cls._parse_title_from_line(file_edl.readline())

		for line_num, line_edl in enumerate(l.rstrip('\n') for l in file_edl.readlines()):

			if not line_edl:
				continue

			try:
				# If starting next event, process event buffer and flush
				if event_buffer and cls._is_begin_new_event(line_edl, current_index):
					events.append(Event.from_string("\n".join(event_buffer)))
					event_buffer=[]
					current_index = 0
				
				# Make note of our current event number if specified
				if line_edl.split()[0].isnumeric():
					current_index=int(line_edl.split()[0])
				
				event_buffer.append(line_edl)

			except Exception as e:
				raise ValueError(f"Line {line_num+2}: {e}")
		
		# Take care of the last little feller.
		# TODO: How to not have to do this?
		if event_buffer:
			events.append(Event.from_string("\n".join(event_buffer)))
		
		return cls(title=title, fcm=Fcm.NON_DROP_FRAME, events=events)
	
	@staticmethod
	def _is_begin_new_event(line:str, current_index:int) -> bool:
		"""Determine if we're beginning a new event with this line"""

		if not current_index:
			return False

		first_token = line.split(maxsplit=1)[0]
		
		# Encountered prefixed form statement while parsing an event
		if first_token.lower() in {"FCM:","SPLIT:"}:
			return True
		
		# Encountered an event number different than the one we been doin'
		elif first_token.isnumeric() and int(first_token) != current_index:
			return True

		return False

	@staticmethod
	def _parse_title_from_line(line:str) -> str:
		"""Extract a title from a line in an EDL"""
		START = "title:"
		if not line.lower().startswith(START):
			raise ValueError("Title was expected, but not found")
		title = line[len(START):].strip()
		if not len(title):
			raise ValueError("Title is empty")
		return title
	
	@staticmethod
	def _parse_fcm_from_line(line:str) -> Fcm:
		"""Extract the FCM from a line in an EDL"""
		START = "fcm:"
		if not line.lower().startswith(START):
			raise ValueError("FCM was expected, but not found")
		try:
			fcm = Fcm(line[len(START):].strip())
		except:
			raise ValueError("Invalid FCM specified")
		return fcm
	
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
		tracks = set()
		for e in self.events:
			tracks = tracks.union(e.tracks)
		return tracks
	
	@property
	def events(self) -> list[Event]:
		"""An EDL event"""
		return self._events
	
	@property
	def sources(self) -> set[SourceReel]:
		"""A set of all sources in the EDL"""
		sources = set()
		for e in self.events:
			sources = sources.union(e.sources)
		return sources
	
	def __str__(self):
		file_text = io.StringIO()
		self.write(file_text)
		return file_text.getvalue()
	
	def __repr__(self):
		return f"<{self.__class__.__name__} title={self.title} FCM={self.fcm} events={len(self.events)}>"