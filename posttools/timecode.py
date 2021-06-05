import enum, re, typing

class InvalidTimecode(Exception):
	"""Timecode has invalid parameters"""

class IncompatibleTimecode(Exception):
	"""Timecode is incompatible with operation"""

class Timecode:
	"""Timecode for video, audio or data"""

	pat_tc = re.compile(r"^([\+\-])?((?:[:;]?\d+){1,4})$")
	
	class Mode(enum.Enum):
		NDF = 1
		DF  = 2

		# TODO: Investigate a better way
		def __str__(self):
			if self == self.NDF: return "NDF"
			else: return "DF"
	
	def __init__(self, timecode:typing.Union[int,str], rate:typing.Union[int,float]=24, mode:typing.Union[Mode,None]=Mode.NDF):

		# Parse rate
		self._rate = round(rate)

		# Set mode
		self._mode = self.Mode(mode) or self.Mode.NDF
		
		# Parse timecode
		if isinstance(timecode, str):
			self._framenumber = self._setFromString(timecode)
		elif isinstance(timecode, int):
			self._framenumber = timecode
		else:
			raise InvalidTimecode("Timecode must be provided as a string or integer value")
		
		# Double-check for sneaky things
		self._validate()

	
	def _setFromString(self, timecode:str):
		"""Frame number from string format: +hh:mm:ss:ff"""

		if self._mode == self.Mode.DF:
			raise NotImplementedError("Parsing NDF timecode from string is not yet supported")

		match = self.pat_tc.match(timecode)
		if not match:
			raise InvalidTimecode("Timecode string is formatted incorrectly")

		negative = match.group(1) == '-'
		tc_groups = [int(x) for x in match.group(2).replace(';',':').strip(':').split(':')]
		framenumber = 0

		while len(tc_groups):
			# Hours
			if len(tc_groups) == 4:
				framenumber += tc_groups.pop(0) * 60 * 60 * self._rate
			# Minutes
			elif len(tc_groups) == 3:
				framenumber += tc_groups.pop(0) * 60 * self._rate
			# Seconds
			elif len(tc_groups) == 2:
				framenumber += tc_groups.pop(0) * self._rate
			# Frames
			elif len(tc_groups) == 1:
				framenumber += tc_groups.pop(0)

		if negative: framenumber *= -1

		return framenumber

	def _validate(self):
		"""Ensure timecode is valid"""

		# Rate check
		if self._rate < 1:
			raise InvalidTimecode("Frame rate must be a positive number")

		# Mode check
		if self._mode == self.Mode.DF and self._rate % 30:
			raise InvalidTimecode("Drop-frame mode only valid for rates divisible by 30")
	
	@property
	def rate(self) -> int:
		"""Timecode frames per second"""
		return self._rate
	
	@property
	def framenumber(self) -> int:
		"""Timecode as number of frames elapsed"""
		return self._framenumber
	
	@property
	def mode(self) -> Mode:
		"""Drop frame mode"""
		return self._mode
	
	@property
	def frames(self) -> int:
		"""Timcode frame number"""
		return int(self._framenumber % self._rate)
	
	@property
	def seconds(self) -> int:
		"""Timecode seconds"""
		return int(self._framenumber / self._rate % 60)
	
	@property
	def minutes(self) -> int:
		"""Timecode minutes"""
		return int(self._framenumber / self._rate / 60 % 60)
	
	@property
	def hours(self) -> int:
		"""Timecode hours"""
		return int(self._framenumber / self._rate / 60 / 60)
	
	@property
	def is_negative(self) -> bool:
		"""Is timecode negative"""
		return self._framenumber < 0
	
	@property
	def is_positive(self) -> bool:
		"""Is timecode positive"""
		return not self.is_negative
	
	def __str__(self):
		if self._mode == self.Mode.DF:
			raise NotImplementedError("NDF timecode string is not yet formatted")
		return f"{'-' if self._framenumber < 0 else ''}{str(abs(self.hours)).zfill(2)}:{str(abs(self.minutes)).zfill(2)}:{str(abs(self.seconds)).zfill(2)}{';' if self._mode == self.Mode.DF else ':'}{str(abs(self.frames)).zfill(2)}"

	def __repr__(self):
		return f"<{str(self)} @ {self._rate}fps {self._mode}>"

	def is_compatible(self, other) -> bool:
		return self.mode == other.mode and self.rate == other.rate
	
	def __add__(self, other):
		"""Add two compatible timecodes"""
		if not self.is_compatible(other):
			raise IncompatibleTimecode("Timecodes must share frame rates and drop frame modes")
		return Timecode(self.framenumber + other.framenumber, self.rate, self.mode)

	def __sub__(self, other):
		"""Subtract two compatible timecodes"""
		if not self.is_compatible(other):
			raise IncompatibleTimecode("Timecodes must share frame rates and drop frame modes")
		return Timecode(self.framenumber - other.framenumber, self.rate, self.mode)
	
	def __eq__(self, other) -> bool:
		"""Confirm two timecodes are equal"""
		return self.is_compatible(other) and self.framenumber == other.framenumber
	
	def __lt__(self, other) -> bool:
		"""Confirm timecode is less than another"""
		return self.is_compatible(other) and self.framenumber < other.framenumber

	def __gt__(self, other) -> bool:
		"""Confirm timecode is greater than another"""
		return self.is_compatible(other) and self.framenumber > other.framenumber
	
	def __le__(self, other) -> bool:
		return self.is_compatible(other) and self.framenumber <= other.framenumber
	
	def __ge__(self, other) -> bool:
		return self.is_compatible(other) and self.framenumber >= other.framenumber


class TimecodeRange:
	"""Timecode range with start, end, and duration"""

	def __init__(self, start:Timecode, end:typing.Union[Timecode,None]=None, duration:typing.Union[Timecode,None]=None):
		self._start = start
		
		if isinstance(end, Timecode):
			self._duration = end - self._start
		elif isinstance(duration, Timecode):
			self._duration = duration
		else:
			raise ValueError("Must supply one of end or duration")
		
		# Validate timecode compatibility
		if self._duration.is_negative:
			raise ValueError("End timecode must occur after start timecode")
		
		if self._start.mode != self._duration.mode:
			raise IncompatibleTimecode("Drop frame modes must match")
		
		if self._start.rate != self._duration.rate:
			raise IncompatibleTimecode("Timecode rates must match")
		
	
	@property
	def start(self) -> Timecode:
		"""Timecode start"""
		return self._start
	
	@property
	def end(self) -> Timecode:
		"""Timecode end"""
		return self._start + self._duration
	
	@property
	def duration(self) -> Timecode:
		"""Timecode duration"""
		return self._duration
	
	@property
	def mode(self) -> Timecode.Mode:
		"""Drop frame mode"""
		return self._start.mode
	
	@property
	def rate(self) -> int:
		"""Timecode rate"""
		return self._start.rate

	def __eq__(self, other) -> bool:
		return self.start.is_compatible(other.start) and self.start.framenumber == other.start.framenumber and self.duration.framenumber == other.duration.framenumber
	
	def __lt__(self,  other) -> bool:
		return self.start.is_compatible(other.start) and self.start < other.start

	def __gt__(self,  other) -> bool:
		return self.start.is_compatible(other.start) and self.start > other.start
	
	def __contains__(self, other) -> bool:
		return self.start <= other.start and self.end >= other.end

	def __repr__(self) -> str:
		return f"<TimecodeRange {self}>"
	
	def __str__(self) -> str:
		return f"{self.start}-{self.end} {self.rate}fps {self.mode}"
	
	def __iter__(self) -> Timecode:
		for frame in range(self.start.framenumber, self.end.framenumber):
			yield Timecode(frame, self.rate, self.mode)
	