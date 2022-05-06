from enum import IntEnum, auto
from typing import Type, Dict, Any, Callable, Tuple, List, Optional

from ..algorithm import BaseAlgorithm


class RunnerStatus(IntEnum):
    INIT = auto()  # init(algo_cls, settings, func)
    INIT_OK = auto()  # init_ok(input_concerns, result_concerns)

    STEP = auto()  # step(step_id, input_config)
    STEP_OK = auto()  # step_ok(retval)
    STEP_FAIL = auto()  # step_fail(error)
    STEP_FINAL = auto()  # step_final(ranklist)

    TRY = auto()  # try(try_id, max_try)
    TRY_COMPLETE = auto()  # try_complete(stdout, stderr, metrics)
    TRY_OK = auto()  # try_ok(retval)
    TRY_FAIL = auto()  # try_fail(error)

    RUN_COMPLETE = auto()  # run_complete(is_cond_meet)


class RunnerEventSet:
    def init(self, algo_cls: Type[BaseAlgorithm], settings: Dict[str, Any], func: Callable):
        pass  # pragma: no cover

    def init_ok(self, input_concerns: Dict[Tuple[Any, ...], Callable],
                result_concerns: Dict[str, Callable]):
        pass  # pragma: no cover

    def step(self, step_id: int, input_config: Any):
        pass  # pragma: no cover

    def step_ok(self, retval: Any, metrics: Any):
        pass  # pragma: no cover

    def step_fail(self, error: Exception):
        pass  # pragma: no cover

    def step_final(self, ranklist: List[Tuple[int, Any, Any]]):
        pass  # pragma: no cover

    def try_(self, try_id: int, max_try: int):
        pass  # pragma: no cover

    def try_complete(self, stdout: Optional[str], stderr: Optional[str], metrics: Dict[str, Any]):
        pass  # pragma: no cover

    def try_ok(self, retval: Any):
        pass  # pragma: no cover

    def try_fail(self, error: Exception):
        pass  # pragma: no cover

    def run_complete(self, is_cond_meet: bool):
        pass  # pragma: no cover
