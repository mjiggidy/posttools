import enum, re, typing

class InvalidTimecode(Exception):
	"""Timecode has invalid parameters"""

class Timecode:
	"""Timecode for video, audio or data"""

	pat_tc = re.compile(r"^([\+\-])?((?:[:;]?\d+){1,4})$")
	
	class Mode(enum.Enum):
		NDF = 1
		DF  = 2
	
	def __init__(self, timecode:typing.Union[int,str], rate:typing.Union[int,float,None]=24, mode:typing.Union[Mode,None]=Mode.NDF):

		# Parse rate
		self._rate = round(rate)

		# Set mode
		self._mode = self.Mode(mode) or self.Mode.NDF
		
		# Parse timecode
		if isinstance(timecode, str):
			self._framenumber = self._setFromString(timecode)
		elif isinstance(int, timecode):
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
	
	def __str__(self):
		if self._mode == self.Mode.DF:
			raise NotImplementedError("NDF timecode string is not yet formatted")

		framenumber = abs(self._framenumber)
		frames  = framenumber % self._rate
		seconds = framenumber / 60 % 60
		minutes = framenumber / 60 / 60 % 60
		hours   = framenumber / 60 / 60 / 24

		return f"{'-' if self._framenumber < 0 else ''}{hours}:{minutes}:{seconds}{';' if self._mode == self.Mode.DF else ':'}{frames}"


	def __repr__(self):
		return f"<{self._framenumber} @ {self._rate}fps {self._mode}>"