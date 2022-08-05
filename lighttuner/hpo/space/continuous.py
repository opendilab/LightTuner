from .base import BaseSpace


class ContinuousSpace(BaseSpace):
    """
    Overview:
        Continuous space.
    """

    def __init__(self, lower, upper):
        """
        Constructor of :class:`ContinuousSpace`.

        :param lower: Left bound.
        :param upper: Right bound.
        """
        self.__lower = float(lower)
        self.__upper = float(upper)

    @property
    def lbound(self) -> float:
        return self.__lower

    @property
    def ubound(self) -> float:
        return self.__upper

    @property
    def length(self) -> float:
        return self.__upper - self.__lower

    @property
    def count(self):
        return None
