from typing import Type, Dict, Any, Callable, Tuple, List

from hbutils.model import AutoIntEnum

from ..old_algorithm import BaseAlgorithm


# noinspection PyArgumentList
class RunnerStatus(AutoIntEnum):
    def __init__(self, func_name: str):
        self.func_name = func_name

    INIT = 'init'  # init(algo_cls, settings, func, spaces, concerns)
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

    def init_ok(self, spaces: Any, concerns: List[Tuple[str, Callable]]):
        pass  # pragma: no cover

    # running stage
    def run_start(self):
        pass  # pragma: no cover

    def run_complete(self, is_cond_meet: bool):
        pass  # pragma: no cover

    # step stage
    def step(self, step_id: int, input_config: Any):
        pass  # pragma: no cover

    def step_ok(self, retval: Any, metrics: Dict[str, Any]):
        pass  # pragma: no cover

    def step_fail(self, error: Exception, metrics: Dict[str, Any]):
        pass  # pragma: no cover

    def step_skip(self, args: Tuple[Any, ...], metrics: Dict[str, Any]):
        pass  # pragma: no cover

    def step_final(self, ranklist: List[Tuple[int, Any, Any]]):
        pass  # pragma: no cover

    # try stage
    def try_(self, try_id: int, max_try: int):
        pass  # pragma: no cover

    def try_complete(self, metrics: Dict[str, Any]):
        pass  # pragma: no cover

    def try_ok(self, retval: Any):
        pass  # pragma: no cover

    def try_skip(self, args: Tuple[Any, ...]):
        pass  # pragma: no cover

    def try_fail(self, error: Exception):
        pass  # pragma: no cover
