import time
from textwrap import dedent
from typing import Type, Dict, Any, Callable, Tuple, Optional, Iterable, List

import inflection
from hbutils.collection import nested_walk
from hbutils.scale import time_to_delta_str
from hbutils.string import plural_word

from .event import RunnerEventSet
from .model import RunResult, RunSkipped, RunFailed
from .result import R as _OR, _to_callable
from .result import _ResultExpression
from ..algorithm import BaseAlgorithm, Task
from ..utils import rchain, RankList
from ..value import HyperValue
from ...logging import getLogger, try_init_root


def _find_hv(vs):
    for path, obj in nested_walk(vs):
        if isinstance(obj, HyperValue):
            r = _OR
            for pitem in path:
                r = r[pitem]
            yield path, r


class LoggingEventSet(RunnerEventSet):

    def __init__(self, name: Optional[str]):
        try_init_root()
        self._logger = getLogger(name)

        self._algorithm_class: Optional[Type[BaseAlgorithm]] = None
        self._func = None
        self._start_time: Optional[float] = None

        self._target_name: Optional[str] = None
        self._params: Optional[List[Tuple[str, _ResultExpression]]] = None
        self._concerns: Optional[List[Tuple[str, _ResultExpression]]] = None

    def init(self, algo_cls: Type[BaseAlgorithm], settings: Dict[str, Any], func: Callable):
        self._algorithm_class = algo_cls
        self._func = func
        setting_text = rchain(sorted((name, val) for name, val in settings.items()))
        self._logger.info(
            f"{self._algorithm_class.algorithm_name()} will be used, "
            f"with [bold bright_white underline]{setting_text}[/]".capitalize()
        )

    def init_ok(
        self, target_name: str, params: Iterable[Tuple[str, _ResultExpression]],
        concerns: Iterable[Tuple[str, _ResultExpression]]
    ):
        self._target_name = target_name
        self._params = params
        self._concerns = concerns
        self._logger.info(f'{self._algorithm_class.algorithm_name()} initialized.'.capitalize())

    def run_start(self):
        self._start_time = time.time()
        self._logger.info('Optimization will be started soon.')

    def run_complete(self, is_cond_meet: bool):
        if is_cond_meet:
            self._logger.info('Stop condition is meet, search will be ended...')
        else:
            self._logger.info('Iteration is over, search will be ended...')

    def step(self, task: Task):
        _data = {'config': task.config}
        cfg_display_values = [(name, _to_callable(param)(_data)) for name, param in self._params]
        self._logger.info(
            dedent(
                f"""
            ======================= {inflection.ordinalize(task.task_id)} step =======================
            Step initialized, with variables - [bold bright_white underline]{rchain(cfg_display_values)}[/].
        """
            ).strip()
        )

    def step_ok(self, task: Task, result: RunResult):
        r_time_cost = result.metrics['time']
        res_display_values = [
            (self._target_name, result.value), *((name, result.get(concern)) for name, concern in self._concerns)
        ]

        self._logger.info(
            dedent(
                f"""
            Function running [green]completed[/], time cost: {"%.3f" % r_time_cost} seconds,
            with concerned results - [bold bright_white underline]{rchain(res_display_values)}[/].
        """
            ).strip()
        )

    def step_fail(self, task: Task, error: RunFailed):
        r_time_cost = error.metrics['time']
        # noinspection PyBroadException
        try:
            raise error
        except:
            self._logger.exception(
                f'Function running [red]failed[/], '
                f'time cost: {r_time_cost:.3f} seconds, '
                f'this step will be skipped and ignored due to this failure.'
            )

    def step_skip(self, task: Task, error: RunSkipped):
        r_time_cost = error.metrics['time']
        self._logger.info(
            dedent(
                f"""
            Sample [yellow]skipped[/], time cost: {"%.3f" % r_time_cost} seconds,
            with arguments: [bold bright_white underline]{error.args!r}[/].
        """
            ).strip()
        )

    def step_final(self, task: Task, ranklist: RankList):
        self._logger.info(
            dedent(f"""
Current ranklist ({plural_word(len(ranklist), 'best record')}):
{ranklist}
        """).strip()
        )
        self._logger.info(
            dedent(
                f"""
            This search task has been lasted for {time_to_delta_str(time.time() - self._start_time)}.

        """.lstrip()
            )
        )

    def try_(self, task: Task, try_id: int, max_try: int):
        self._logger.info(f"Start the {inflection.ordinalize(try_id + 1)} running try of function {self._func}...")

    def try_complete(self, task: Task, try_id: int, max_try: int, metrics: Dict[str, Any]):
        pass

    def try_ok(self, task: Task, try_id: int, max_try: int, retval: Any, metrics: Dict[str, Any]):
        pass

    def try_fail(self, task: Task, try_id: int, max_try: int, error: Exception, metrics: Dict[str, Any]):
        if try_id + 1 < max_try:
            try_again_str = 'will try again later'
        else:
            try_again_str = 'max retry limit is reached'
        error_str = escape(repr(error))
        time_count = f"{try_id + 1}/{max_try}"

        self._logger.warning(f"[yellow]Error has occurred[/] - {error_str}, {try_again_str} ({time_count})...")

    def try_skip(self, task: Task, try_id: int, max_try: int, args: Tuple[Any, ...], metrics: Dict[str, Any]):
        pass


def escape(s: str) -> str:
    return s.replace('[', '\\[')
