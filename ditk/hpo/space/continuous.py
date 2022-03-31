from typing import Tuple, Union

from .base import BaseSpace, ALLOC_UNLIMITED

DEFAULT_COUNT = 5


class ContinuousSpace(BaseSpace):
    """
    Overview:
        Continuous space.
    """
    __priority__ = 1

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

    def allocate(self, cnt: int = ALLOC_UNLIMITED) -> Tuple[Union[int, float], ...]:
        """
        Allocate the values in this continuous space.

        :param cnt: Count of allocating values.
        :return: Tuple of values.
        
        Examples:: 
            >>> from ditk.hpo.space import ContinuousSpace
            >>> space = ContinuousSpace(0.4, 2.2)
            >>> space.allocate()  # default count is 5
            (0.4, 0.85, 1.3, 1.75, 2.2)
            >>> space.allocate(0)
            ()
            >>> space.allocate(1)
            (1.3,)
            >>> space.allocate(2)
            (0.4, 2.2)
            >>> space.allocate(3)
            (0.4, 1.3, 2.2)
            >>> space.allocate(4)
            (0.4, 1.0, 1.6, 2.2)
            >>> space.allocate(5)
            (0.4, 0.85, 1.3, 1.75, 2.2)
            >>> space.allocate(6)
            (0.4, 0.76, 1.12, 1.48, 1.84, 2.2)
            >>> space.allocate(7)
            (0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2)
            >>> space.allocate(9)
            (0.4, 0.625, 0.85, 1.075, 1.3, 1.525, 1.75, 1.975, 2.2)
            >>> space.allocate(10)
            (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2)
            >>> space.allocate(11)
            (0.4, 0.58, 0.76, 0.94, 1.12, 1.3, 1.48, 1.66, 1.84, 2.02, 2.2)
        """
        if cnt == ALLOC_UNLIMITED:
            return self.allocate(DEFAULT_COUNT)
        elif cnt == 0:
            return ()
        elif cnt == 1:
            return ((self.__l + self.__r) / 2,)
        else:
            return tuple(map(lambda x: (x / (cnt - 1)) * (self.__r - self.__l) + self.__l, range(cnt)))
