from typing import Type, Dict, Any, Callable, Tuple, Iterable

from hbutils.model import AutoIntEnum

from .model import RunResult, RunFailed, RunSkipped
from .result import _ResultExpression
from ..algorithm import Task, BaseAlgorithm
# noinspection PyArgumentList
from ..utils import RankList


class RunnerStatus(AutoIntEnum):

    def __init__(self, func_name: str):
        self.func_name = func_name

    INIT = 'init'  # init(algo_cls, settings, func, spaces)
    INIT_OK = 'init_ok'  # init_ok(input_concerns, result_concerns)

    RUN_START = 'run_start'  # run_start()
    RUN_COMPLETE = 'run_complete'  # run_complete(is_cond_meet)

    STEP = 'step'  # step(step_id, input_config)
    STEP_OK = 'step_ok'  # step_ok(retval, metrics)
    STEP_FAIL = 'step_fail'  # step_fail(error, metrics)
    STEP_SKIP = 'step_skip'  # step_skip(error, args)
    STEP_FINAL = 'step_final'  # step_final(ranklist)

    TRY = 'try_'  # try(try_id, max_try)
    TRY_COMPLETE = 'try_complete'  # try_complete(metrics)
    TRY_OK = 'try_ok'  # try_ok(retval)
    TRY_FAIL = 'try_fail'  # try_fail(error)
    TRY_SKIP = 'try_skip'  # try_skip(args)


class RunnerEventSet:
    # init stage
    def init(self, algo_cls: Type[BaseAlgorithm], settings: Dict[str, Any], func: Callable):
        pass  # pragma: no cover

    def init_ok(
        self, target_name: str, params: Iterable[Tuple[str, _ResultExpression]],
        concerns: Iterable[Tuple[str, _ResultExpression]]
    ):
        pass  # pragma: no cover

    # running stage
    def run_start(self):
        pass  # pragma: no cover

    def run_complete(self, is_cond_meet: bool):
        pass  # pragma: no cover

    # step stage
    def step(self, task: Task):
        pass  # pragma: no cover

    def step_ok(self, task: Task, result: RunResult):
        pass  # pragma: no cover

    def step_fail(self, task: Task, error: RunFailed):
        pass  # pragma: no cover

    def step_skip(self, task: Task, error: RunSkipped):
        pass  # pragma: no cover

    def step_final(self, task: Task, ranklist: RankList):
        pass  # pragma: no cover

    # try stage
    def try_(self, task: Task, try_id: int, max_try: int):
        pass  # pragma: no cover

    def try_complete(self, task: Task, try_id: int, max_try: int, metrics: Dict[str, Any]):
        pass  # pragma: no cover

    def try_ok(self, task: Task, try_id: int, max_try: int, retval: Any, metrics: Dict[str, Any]):
        pass  # pragma: no cover

    def try_fail(self, task: Task, try_id: int, max_try: int, error: Exception, metrics: Dict[str, Any]):
        pass  # pragma: no cover

    def try_skip(self, task: Task, try_id: int, max_try: int, args: Tuple[Any, ...], metrics: Dict[str, Any]):
        pass  # pragma: no cover
