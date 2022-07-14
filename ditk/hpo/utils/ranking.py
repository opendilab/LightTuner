import bisect
from collections.abc import Sequence as _MetaSequence
from typing import Tuple, Callable, Sequence, Optional

from tabulate import tabulate


class RankList(_MetaSequence):

    def __init__(
        self,
        capacity: int,
        columns: Sequence[Tuple[str, Callable]],
        init: Optional[Sequence] = None,
        key: Optional[Callable] = None,
        reverse: bool = False,
        tablefmt: str = 'psql'
    ):
        self.__capacity = capacity
        self.__columns = columns
        key = key or (lambda x: x)
        self.__key = (lambda x: -key(x)) if reverse else key
        self.__tablefmt = tablefmt

        self.__rows = []
        self._max_id = 0
        if init:
            self.__init(init or [])

    def __init(self, items):
        _actual = []
        for item in items:
            self._max_id += 1
            _actual_item = (self.__key(item), self._max_id, item)
            _actual.append(_actual_item)

        self.__rows = sorted(_actual)[:self.__capacity]

    def append(self, item):
        self._max_id += 1
        _actual_item = (self.__key(item), self._max_id, item)
        _insert_index = bisect.bisect_right(self.__rows, _actual_item)
        self.__rows.insert(_insert_index, _actual_item)
        while len(self.__rows) > self.__capacity:
            self.__rows.pop()

    def __len__(self):
        return self.__rows.__len__()

    def __getitem__(self, item):
        return [row for _, _, row in self.__rows].__getitem__(item)

    def __str__(self):
        return tabulate(
            [[name_key(row) for _, name_key in self.__columns] for row in self],
            headers=[name for name, _ in self.__columns],
            tablefmt=self.__tablefmt,
        )
