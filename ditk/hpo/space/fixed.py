from .base import BaseSpace


class FixedSpace(BaseSpace):
    """
    Overview:
        Fixed space.

        .. note::
            Can be used to drive the enumeration.
    """

    def __init__(self, n):
        """
        Constructor of :class:`FixedSpace`.

        :param n: Count of values.
        """
        self.__n = n

    @property
    def length(self) -> int:
        return self.__n

    @property
    def count(self) -> int:
        return self.__n
