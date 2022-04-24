from typing import Union, Optional


class BaseSpace:
    """
    Overview:
        Base class of spaces.

        .. warning::
            This is an abstract class, do not use.
    """

    @property
    def length(self) -> Union[int, float]:
        """
        Length of space.
        """
        raise NotImplementedError  # pragma: no cover

    @property
    def count(self) -> Optional[int]:
        """
        Count of elements in space.
        """
        raise NotImplementedError  # pragma: no cover
