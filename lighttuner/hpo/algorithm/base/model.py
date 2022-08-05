from collections import namedtuple
from enum import IntEnum, unique

from hbutils.model import int_enum_loads


@int_enum_loads(name_preprocess=str.upper)
@unique
class OptimizeDirection(IntEnum):
    MAXIMIZE = 1
    MINIMIZE = 2


Task = namedtuple('Task', ('task_id', 'config', 'attachment'))
