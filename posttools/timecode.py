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
	
	def __init__(self, timecode:typing.Union[int,str], rate:typing.Union[int,float]=24, mode:typing.Optional[Mode]=Mode.NDF):

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
	def _df_offset(self) -> int:
		"""Calculate frame offset for drop frame"""
		
		if self._mode != self.Mode.DF:
			return 0

		framenumber_normalized = abs(self._framenumber)
		neg = -1 if self.is_negative else 1
		
		# Drop-frame adds two frames every minute, except every ten minutes
		# First: Let's get some things straight
		drop_offset = (2 * self._rate // 30)			# Frames to drop -- 2 per 30fps
		
		full_minute = self._rate * 60					# Length of a full non-drop minute (in frames) (60 seconds)
		drop_minute = full_minute - drop_offset			# Length of a drop-minute (in frames)
		drop_segment = full_minute + (drop_minute * 9)	# Length of a drop-segment (in frames) (One full minute + Nine drop minutes = 10 Minutes)
		
		# So how many full 10-minute drop-segments have elapsed
		drop_segments_elapsed = framenumber_normalized // drop_segment

		# And as for the remaining frames at the end...
		remaining_frames = framenumber_normalized % drop_segment
		remaining_drop_frames = max(remaining_frames - full_minute + 1, 0)	# I don't understand why +1 yet, but that was a problem for like three days. max() will be bad for negative values
		
		# Number of complete drop-minutes
		drop_minutes_elapsed = remaining_drop_frames // drop_minute

		# And then any other frames will need a 2-frame boost! Oooh!
		remainder = drop_offset if (remaining_drop_frames % drop_minute) else 0


		return ((drop_segments_elapsed * (9 * drop_offset)) + (drop_minutes_elapsed * drop_offset) + remainder) * neg + (self._rate // 30 if self.is_negative else 0)

	
	@property
	def rate(self) -> int:
		"""Timecode frames per second"""
		return self._rate
	
	@property
	def framenumber(self) -> int:
		"""Timecode as number of frames elapsed"""
		return self._framenumber

	@property
	def formatted(self, rollover:bool=False) -> str:
		"""Retrieve the timecode as a string with hh:mm:ss:ff formatting"""
		# TODO: Implement `rollover` flag
		# TODO: Implement `signed` flag
		
		sign = '-' if self._framenumber < 0 else ''
		separator = ';' if self._mode == self.Mode.DF else ':'
		df_offset = self._df_offset

		return f"{sign}{abs(self.hours):02d}:{abs(self.minutes):02d}:{abs(self.seconds):02d}{separator}{abs(self.frames):02d}"


	@property
	def mode(self) -> Mode:
		"""Drop frame mode"""
		return self._mode
	
	@property
	def frames(self, df_offset:int=None) -> int:
		"""Timcode frame number"""
		# TODO: I don't think I can do this df_offset thing with a @property
		df_offset = df_offset or self._df_offset
		return int((self._framenumber + df_offset) % self._rate)
	
	@property
	def seconds(self, df_offset:int=None) -> int:
		"""Timecode seconds"""
		df_offset = df_offset or self._df_offset
		return int((self._framenumber + df_offset) / self._rate % 60)
	
	@property
	def minutes(self, df_offset:int=None) -> int:
		"""Timecode minutes"""
		df_offset = df_offset or self._df_offset
		return int((self._framenumber + df_offset) / self._rate / 60 % 60)
	
	@property
	def hours(self, df_offset:int=None) -> int:
		"""Timecode hours"""
		df_offset = df_offset or self._df_offset
		return int((self._framenumber + df_offset) / self._rate / 60 / 60)
	
	@property
	def is_negative(self) -> bool:
		"""Is timecode negative"""
		return self._framenumber < 0
	
	@property
	def is_positive(self) -> bool:
		"""Is timecode positive"""
		return not self.is_negative
	
	def __str__(self):
		return self.formatted

	def __repr__(self):
		return f"<{self.__class__.__name__} {str(self)} @ {self._rate}fps {self._mode}>"

	def is_compatible(self, other) -> bool:
		return isinstance(other, self.__class__) and self.mode == other.mode and self.rate == other.rate
	
	def __add__(self, other):
		"""Add two compatible timecodes"""
		if self.is_compatible(other):
			return Timecode(self.framenumber + other.framenumber, self.rate, self.mode)
		elif isinstance(other, str):
			return self +  Timecode(other, self.rate, self.mode)
		elif isinstance(other, int):
			return Timecode(self.framenumber + other, self.rate, self.mode)
		else:
			raise IncompatibleTimecode("Timecodes must share frame rates and drop frame modes")

	def __sub__(self, other):
		"""Subtract two compatible timecodes"""
		if self.is_compatible(other):
			return Timecode(self.framenumber - other.framenumber, self.rate, self.mode)
		elif isinstance(other, int):
			return Timecode(self.framenumber - other, self.rate, self.mode)
		elif isinstance(other, str):
			return self - Timecode(other, self.rate, self.mode)
		else:
			raise IncompatibleTimecode("Timecodes must share frame rates and drop frame modes")
	
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

	def __init__(self, start:Timecode, end:typing.Optional[Timecode]=None, duration:typing.Optional[Timecode]=None):
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
		return f"<{self.__class__.__name__} {self}>"
	
	def __str__(self) -> str:
		return f"{self.start}-{self.end} {self.rate}fps {self.mode}"
	
	def __iter__(self) -> Timecode:
		for frame in range(self.start.framenumber, self.end.framenumber):
			yield Timecode(frame, self.rate, self.mode)
	