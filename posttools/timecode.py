import enum, re, typing

class InvalidTimecode(Exception):
	"""Timecode has invalid parameters"""

class IncompatibleTimecode(Exception):
	"""Timecode is incompatible with operation"""

class Timecode:
	"""Timecode for video, audio or data"""

	pat_tc = re.compile(r"^([\+\-])?((?:[:;]?\d+){1,4})$")
	
	class Mode(enum.IntEnum):
		NDF = 1
		DF  = 2
	
	def __init__(self, timecode:typing.Union[int,str], rate:typing.Union[int,float]=24, mode:typing.Optional[Mode]=Mode.NDF):
		"""Timecode for video, audio or data"""
		# Parse rate
		self._rate = round(rate)

		# Set mode
		self._mode = self.Mode(mode) or self.Mode.NDF
		
		# Parse timecode
		if isinstance(timecode, str):
			self._framenumber = self._setFromString(timecode)
			#if self.mode is self.Mode.DF: self._framenumber -= round(self._framenumber * 0.06666)
		elif isinstance(timecode, int):
			self._framenumber = timecode
		else:
			raise InvalidTimecode("Timecode must be provided as a string or integer value")
		
		# Double-check for sneaky things
		self._validate()

	
	def _setFromString(self, timecode:str):
		"""Frame number from string format: +hh:mm:ss:ff"""


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

	def _df_offset(self, force_offset:bool=False) -> int:
		"""Calculate frame offset for drop frame"""
		
		if self._mode != self.Mode.DF and force_offset != True:
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
		df_offset = self._df_offset()

		return f"{sign}{abs(self.hours):02d}:{abs(self.minutes):02d}:{abs(self.seconds):02d}{separator}{abs(self.frames):02d}"


	@property
	def mode(self) -> Mode:
		"""Drop frame mode"""
		return self._mode
	
	@property
	def frames(self, df_offset:typing.Optional[int]=None) -> int:
		"""Timcode frame number"""
		# TODO: I don't think I can do this df_offset thing with a @property
		df_offset = df_offset or self._df_offset()
		return int((self._framenumber + df_offset) % self._rate)
	
	@property
	def seconds(self, df_offset:typing.Optional[int]=None) -> int:
		"""Timecode seconds"""
		df_offset = df_offset or self._df_offset()
		return int((self._framenumber + df_offset) / self._rate % 60)
	
	@property
	def minutes(self, df_offset:typing.Optional[int]=None) -> int:
		"""Timecode minutes"""
		df_offset = df_offset or self._df_offset()
		return int((self._framenumber + df_offset) / self._rate / 60 % 60)
	
	@property
	def hours(self, df_offset:typing.Optional[int]=None) -> int:
		"""Timecode hours"""
		df_offset = df_offset or self._df_offset()
		return int((self._framenumber + df_offset) / self._rate / 60 / 60)
	
	@property
	def is_negative(self) -> bool:
		"""Is timecode negative"""
		return self._framenumber < 0
	
	@property
	def is_positive(self) -> bool:
		"""Is timecode positive"""
		return not self.is_negative
	
	# Utility methods
	def resample(self, rate:typing.Union[int,float,None]=None, mode:typing.Optional[Mode]=None) -> "Timecode":
		"""Resample timecode to a new rate/mode"""
		new_rate = rate or self._rate
		new_mode = mode or self._mode

		if new_rate == self._rate and new_mode == self._mode:
			return self

		factor = new_rate / self._rate

		# For drop-frame conversions, apply or remove the dropped frame offset


		"""
		if self._mode == self.Mode.DF and new_mode == self.Mode.NDF:
			df_offset = self._df_offset()
			old_framenumber = self._framenumber + df_offset

		elif self._mode == self.Mode.NDF and new_mode == self.Mode.DF:
			df_offset = self._df_offset(True)
			print(df_offset)
			old_framenumber = self._framenumber - df_offset
		"""

		if self._mode == self.Mode.DF or new_mode == self.Mode.DF:
			raise NotImplementedError("No DF not yet too hard")
			
		else:
			old_framenumber = self._framenumber
			
		
		return Timecode(round(old_framenumber * factor), new_rate, new_mode)


	
	def __str__(self):
		return self.formatted

	def __repr__(self):
		return f"<{self.__class__.__name__} {str(self)} @ {self._rate}fps {self._mode.name}>"

	def _is_compatible(self, other) -> bool:
		return isinstance(other, self.__class__) and self.mode == other.mode and self.rate == other.rate
	
	def _cmp_normalize(self, other:typing.Any) -> "Timecode":
		"""Normalize addend for math comparisons"""
		
		if isinstance(other, Timecode):
			return other
		
		# Attempt to create a new Timecode object with matching rate and mode
		# Enjoy the InvalidTimecode exception if this doesn't work
		return Timecode(other, self._rate, self._mode)

	
	def __add__(self, other:typing.Any) -> "Timecode":
		"""Adds a timecode

		If the second addend is of a different rate or mode, it will be converted to the same as the first addend.
		"""
		other = self._cmp_normalize(other).resample(self._rate, self._mode)
		return Timecode(self._framenumber + other._framenumber, self._rate, self._mode)

	def __sub__(self, other) -> "Timecode":
		"""Subtracts a timecode

		If the subtrahend is of a different rate or mode, it will be converted to the same as the minuend.
		"""
		other = self._cmp_normalize(other).resample(self._rate, self._mode)
		return Timecode(self._framenumber - other._framenumber, self._rate, self._mode)

	def __eq__(self, other) -> bool:
		"""Confirm two timecodes are equal in frame, rate, and mode"""
		other = self._cmp_normalize(other)
		return self._is_compatible(other) and self._framenumber == other._framenumber
	
	def __lt__(self, other) -> bool:
		"""Confirm this timecode is less than another
		
		Precedence: NDF < DF; frame rate; frame number
		"""
		other = self._cmp_normalize(other)

		if self._mode != other._mode:
			return self._mode < other._mode
		elif self._rate != other._rate:
			return self._rate < other._rate
		else:
			return self._framenumber < other._framenumber

	def __gt__(self, other) -> bool:
		"""Confirm this timecode is greater than another
		
		Precedence: DF > NDF; frame rate; frame number
		"""
		other = self._cmp_normalize(other)

		if self._mode != other._mode:
			return self._mode > other._mode
		elif self._rate != other._rate:
			return self._rate > other._rate
		else:
			return self._framenumber > other._framenumber
	
	def __le__(self, other) -> bool:
		"""Confirm this timecode is less than or equal to another
		
		Precedence: NDF < DF; frame rate; frame number
		"""
		other = self._cmp_normalize(other)
		if self._mode > other._mode:
			return False
		elif self._rate > other._rate:
			return False
		else:
			return self._framenumber <= other._framenumber
	
	def __ge__(self, other) -> bool:
		"""Confirm this timecode is greater than or equal to another
		
		Precedence: DF > NDF; frame rate; frame number
		"""
		if self._mode < other._mode:
			return False
		elif self._rate < other._rate:
			return False
		else:
			return self._framenumber >= other._framenumber
	
	def __hash__(self) -> int:
		"""Create a unique hash for this timecode"""
		return hash((self._framenumber, self._rate, self._mode))


class TimecodeRange:
	"""Timecode range with start, end, and duration"""

	def __init__(self, *, start:Timecode, end:typing.Optional[Timecode]=None, duration:typing.Optional[Timecode]=None):
		"""Timecode range with start, end, and duration"""
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
		return self.start._is_compatible(other.start) and self.start.framenumber == other.start.framenumber and self.duration.framenumber == other.duration.framenumber
	
	def __lt__(self,  other) -> bool:
		return self.start._is_compatible(other.start) and self.start < other.start

	def __gt__(self,  other) -> bool:
		return self.start._is_compatible(other.start) and self.start > other.start
	
	def __contains__(self, other) -> bool:
		return self.start <= other.start and self.end >= other.end

	def __repr__(self) -> str:
		return f"<{self.__class__.__name__} {self}>"
	
	def __str__(self) -> str:
		return f"{self.start}-{self.end} {self.rate}fps {self.mode}"
	
	def __iter__(self) -> Timecode:
		for frame in range(self.start.framenumber, self.end.framenumber):
			yield Timecode(frame, self.rate, self.mode)
	