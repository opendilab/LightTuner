from typing import Tuple, Union

from .base import BaseSpace, ALLOC_UNLIMITED


class SeparateSpace(BaseSpace):
    """
    Overview:
        Separated space.
    """
    __priority__ = 2

    def __init__(self, start, end, step):
        """
        Constructor of :class:`SeparateSpace`.

        :param start: Start value.
        :param end: End value.
        :param step: Step interval.
        """
        self.__l = 0
        self.__r = int((end - start) // step)

        self.__start = (self.__l * step) + start
        self.__end = (self.__r * step) + start
        self.__step = step

    @property
    def lbound(self) -> Union[int, float]:
        return self.__start

    @property
    def rbound(self) -> Union[int, float]:
        return self.__end

    def allocate(self, cnt: int = ALLOC_UNLIMITED) -> Tuple[Union[int, float], ...]:
        """
        Allocate the values in this separated space.

        :param cnt: Count of allocating values.
        :return: Tuple of values.

        Examples::
            >>> from ditk.hpo.space import SeparateSpace
            >>> space = SeparateSpace(0.4, 2.2, 0.2)
            >>> space.allocate()
            (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2)
            >>> space.allocate(0)
            ()
            >>> space.allocate(1)
            (1.2,)
            >>> space.allocate(2)
            (0.4, 2.2)
            >>> space.allocate(3)
            (0.4, 1.2, 2.2)
            >>> space.allocate(4)
            (0.4, 1.0, 1.6, 2.2)
            >>> space.allocate(5)
            (0.4, 0.8, 1.2, 1.8, 2.2)
            >>> space.allocate(6)
            (0.4, 0.8, 1.2, 1.4, 1.8, 2.2)
            >>> space.allocate(7)
            (0.4, 0.8, 1.0, 1.2, 1.6, 2.0, 2.2)
            >>> space.allocate(8)
            (0.4, 0.6, 1.0, 1.2, 1.4, 1.6, 2.0, 2.2)
            >>> space.allocate(9)
            (0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 1.8, 2.0, 2.2)
            >>> space.allocate(10)
            (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2)
            >>> space.allocate(11)
            (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2)
            >>> space.allocate(100)
            (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2)
        """
        return tuple(map(lambda x: x * self.__step + self.__start, self._alloc_unit(cnt)))

    def _alloc_unit(self, cnt: int = ALLOC_UNLIMITED):
        if cnt == ALLOC_UNLIMITED:
            return range(self.__l, self.__r + 1)
        elif cnt == 0:
            return ()
        elif cnt == 1:
            return (int(round((self.__l + self.__r) / 2)),)
        else:
            total = self.__r - self.__l + 1
            if cnt >= total:
                return self._alloc_unit(ALLOC_UNLIMITED)
            else:
                unit = (total - 1) * 1.0 / (cnt - 1)
                return map(lambda x: int(round(x * unit)), range(cnt))
