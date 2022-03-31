from typing import Tuple, Union

from .base import BaseSpace, ALLOC_UNLIMITED


class FixedSpace(BaseSpace):
    """
    Overview:
        Fixed space.

        .. note::
            Can be used to drive the enumeration.
    """
    __priority__ = 3

    def __init__(self, n):
        """
        Constructor of :class:`FixedSpace`.

        :param n: Count of values.
        """
        self.__n = n

    @property
    def lbound(self):
        return 0

    @property
    def rbound(self):
        return self.__n - 1

    @property
    def length(self):
        return self.__n

    def allocate(self, cnt: int = ALLOC_UNLIMITED) -> Tuple[Union[int, float], ...]:
        """
        Allocate the values in this space.

        All the values will be returned regardless of ``cnt``'s value.

        :param cnt: Count of allocating values.
        :return: Tuple of values.

        Examples::
            >>> from ditk.hpo.space import FixedSpace
            >>> space = FixedSpace(5)
            >>> space.allocate()
            (0, 1, 2, 3, 4)
            >>> space.allocate(0)
            (0, 1, 2, 3, 4)
            >>> space.allocate(1)
            (0, 1, 2, 3, 4)
            >>> space.allocate(2)
            (0, 1, 2, 3, 4)
            >>> space.allocate(3)
            (0, 1, 2, 3, 4)
            >>> space.allocate(4)
            (0, 1, 2, 3, 4)
            >>> space.allocate(5)
            (0, 1, 2, 3, 4)
            >>> space.allocate(6)
            (0, 1, 2, 3, 4)
            >>> space.allocate(7)
            (0, 1, 2, 3, 4)
        """
        return tuple(range(self.__n))
