import abc
from .shot import Shot

class Shotlist(abc.ABC):
	"""Abstract shot list"""

	shots: list[Shot]
