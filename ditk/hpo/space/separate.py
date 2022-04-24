from .base import BaseSpace


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

        self.__start = float((self.__l * step) + start)
        self.__end = float((self.__r * step) + start)
        self.__step = float(step)

    @property
    def start(self) -> float:
        return self.__start

    @property
    def end(self) -> float:
        return self.__end

    @property
    def step(self) -> float:
        return self.__step

    @property
    def length(self) -> float:
        return self.__end - self.__start

    @property
    def count(self) -> int:
        return self.__r + 1
