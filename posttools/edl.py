import enum, typing, io, re
from multiprocessing.sharedctypes import Value

class Event:
	"""An EDL Event"""
	pat_event = re.compile(r"^(?P<event_number>\d+)\s+(?P<reel_name>[^\s]+)\s+(?P<track_type>A[%\s]*|B|V)\s+(?P<event_type>C|D|W\d+|K\s*[BO]?)\s+(?P<event_duration>\d*)\s+(?P<tc_src_in>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_src_out>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_rec_in>\d{2}:\d{2}:\d{2}:\d{2})\s+(?P<tc_rec_out>\d{2}:\d{2}:\d{2}:\d{2})\s*$", re.I)

class Fcm(enum.Enum):
	"""Frame counting mode of the EDL"""
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
	
	def __init__(self, *, title:str="Untitled EDL", fcm:Fcm=Fcm.NON_DROP_FRAME):

		self._title = title
		self._fcm   = fcm
		self._events = list()

	@classmethod
	def from_file(cls, file:io.BufferedReader):
		"""Create an EDL from an input file stream"""

		mode =_ParseModes.START

		for line_num, line_edl in enumerate(l.rstrip('\n') for l in file.readlines()):

			try:
				if mode == _ParseModes.START:
					mode = _ParseModes.TITLE
					title = cls._parse_title(line_edl)

				elif mode == _ParseModes.TITLE:
					mode = _ParseModes.FCM
					fcm = cls._parse_fcm(line_edl)
				
				elif mode == _ParseModes.FCM:
					break
				
			except Exception as e:
				raise ValueError(f"Line {line_num+1}: {e}")
		
		return cls(title=title, fcm=fcm)
			
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
	
	def write(self, file:io.TextIOBase):
		"""Write the EDL to a given stream"""

		print(f"TITLE: {self.title}", file=file)
		print(f"FCM: {self.fcm.value}", file=file)

		for event in self.events:
			print(event, file=file)

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
	def events(self) -> list[Event]:
		"""An EDL event"""
		return self._events
	
	def __str__(self):
		file_text = io.StringIO()
		self.write(file_text)
		return file_text.getvalue()
	
	def __repr__(self):
		return f"<{self.__class__.__name__} title={self.title} FCM={self.fcm} events={len(self.events)}>"