from .base import BaseSpace


class ContinuousSpace(BaseSpace):
    """
    Overview:
        Continuous space.
    """

    def __init__(self, l, r):
        """
        Constructor of :class:`ContinuousSpace`.

        :param l: Left bound.
        :param r: Right bound.
        """
        self.__l = float(l)
        self.__r = float(r)

    @property
    def lbound(self) -> float:
        return self.__l

    @property
    def rbound(self) -> float:
        return self.__r

    @property
    def length(self) -> float:
        return self.__r - self.__l

    @property
    def count(self):
        return None
