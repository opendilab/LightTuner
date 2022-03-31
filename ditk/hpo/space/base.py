from typing import Tuple, Union

ALLOC_UNLIMITED = -1


class BaseSpace:
    """
    Overview:
        Base class of spaces.

        .. warning::
            This is an abstract class, do not use.
    """
    __priority__ = 0

    @property
    def lbound(self):
        """
        Left bound.
        """
        raise NotImplementedError  # pragma: no cover

    @property
    def rbound(self):
        """
        Right bound.
        """
        raise NotImplementedError  # pragma: no cover

    @property
    def length(self):
        """
        Length of space.
        """
        return self.rbound - self.lbound

    def allocate(self, cnt: int = ALLOC_UNLIMITED) -> Tuple[Union[int, float], ...]:
        """
        Allocate the values in space with the given count ``cnt``.

        :param cnt: Count of values.
        :return: Tuple of values.
        """
        raise NotImplementedError  # pragma: no cover
