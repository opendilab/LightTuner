import time
from textwrap import dedent
from typing import Type, Dict, Any, Callable, Tuple, List, Optional

import inflection
from hbutils.collection import nested_walk
from hbutils.scale import time_to_delta_str
from hbutils.string import plural_word
from tabulate import tabulate

from .event import RunnerEventSet
from .result import R as _OR
from ..old_algorithm import BaseAlgorithm
from ..utils import rchain
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

        self._algorithm_cls: Optional[Type[BaseAlgorithm]] = None
        self._func: Optional[Callable] = None
        self._independents: Optional[List[Tuple[str, Callable]]] = None
        self._dependents: Optional[List[Tuple[str, Callable]]] = None
        self._max_try: Optional[int] = None

        self._current_step_id: Optional[int] = None
        self._current_try_id: Optional[int] = None
        self._start_time: Optional[float] = None

    def init(self, algo_cls: Type[BaseAlgorithm], settings: Dict[str, Any], func: Callable):
        self._algorithm_cls = algo_cls
        self._func = func
        algorithm_name = self._algorithm_cls.algorithm_name()
        setting_text = rchain(sorted((name, val) for name, val in settings.items()))
        self._logger.info(
            f"{algorithm_name} will be used, with [bold bright_white underline]{setting_text}[/]".capitalize())

    def init_ok(self, spaces: Any, concerns: List[Tuple[str, Callable]]):
        self._independents = [('.'.join(map(str, pname)), getter) for pname, getter in _find_hv(spaces)]
        self._dependents = concerns
        algorithm_name = self._algorithm_cls.algorithm_name()
        self._logger.info(f'{algorithm_name} initialized.'.capitalize())

    def run_start(self):
        self._start_time = time.time()
        self._logger.info('Optimization will be started soon.')

    def run_complete(self, is_cond_meet: bool):
        if is_cond_meet:
            self._logger.info('Stop condition is meet, search will be ended...')
        else:
            self._logger.info('Iteration is over, search will be ended...')

    def step(self, step_id: int, input_config: Any):
        self._current_step_id = step_id
        cfg_display_values = [(name, getter(input_config)) for name, getter in self._independents]
        self._logger.info(dedent(f"""
            ======================= {inflection.ordinalize(self._current_step_id)} step =======================
            Step initialized, with variables - [bold bright_white underline]{rchain(cfg_display_values)}[/].
        """).strip())

    def step_ok(self, retval: Any, metrics: Dict[str, Any]):
        r_time_cost = metrics['time']
        full_result = {'return': retval, 'metrics': metrics}
        res_display_values = [(name, getter(full_result)) for name, getter in self._dependents]

        self._logger.info(dedent(f"""
            Function running [green]completed[/], time cost: {"%.3f" % r_time_cost} seconds,
            with concerned results - [bold bright_white underline]{rchain(res_display_values)}[/].
        """).strip())

    def step_fail(self, error: Exception, metrics: Dict[str, Any]):
        r_time_cost = metrics['time']
        # noinspection PyBroadException
        try:
            raise error
        except:
            self._logger.exception(f'Function running [red]failed[/], '
                                   f'time cost: {"%.3f" % r_time_cost} seconds, '
                                   f'this step will be skipped and ignored due to this failure.')

    def step_skip(self, args: Tuple[Any, ...], metrics: Dict[str, Any]):
        r_time_cost = metrics['time']
        self._logger.info(dedent(f"""
            Sample [yellow]skipped[/], time cost: {"%.3f" % r_time_cost} seconds,
            with arguments: [bold bright_white underline]{args!r}[/].
        """).strip())

    def step_final(self, ranklist: List[Tuple[int, Any, Any]]):
        self._logger.info(dedent(f"""
Current ranklist ({plural_word(len(ranklist), 'best record')}):
{escape(self._make_ranklist_table(ranklist))}
        """).strip())
        self._logger.info(dedent(f"""
            This search task has been lasted for {time_to_delta_str(time.time() - self._start_time)}.

        """.lstrip()))

    def try_(self, try_id: int, max_try: int):
        self._current_try_id = try_id
        self._max_try = max_try
        self._logger.info(f"Start the {inflection.ordinalize(try_id + 1)} running try of function {self._func}...")

    def try_complete(self, metrics: Dict[str, Any]):
        pass

    def try_ok(self, retval: Any):
        pass

    def try_skip(self, args: Tuple[Any, ...]):
        pass

    def try_fail(self, error: Exception):
        if (self._current_try_id + 1) < self._max_try:
            try_again_str = f'will try again later'
        else:
            try_again_str = f'max retry limit is reached'
        error_str = escape(repr(error))
        time_count = f"{self._current_try_id + 1}/{self._max_try}"

        self._logger.warning(f"[yellow]Error has occurred[/] - {error_str}, {try_again_str} ({time_count})...")

    def _make_ranklist_table(self, ranklist) -> str:
        return tabulate(
            [
                [
                    istep,
                    *(getter(cfg) for _, getter in self._independents),
                    *(getter(fres) for _, getter in self._dependents),
                ] for istep, cfg, fres in ranklist],
            headers=[
                '#',
                *(name for name, _ in self._independents),
                *(name for name, _ in self._dependents)
            ], tablefmt='psql'
        )


def escape(s: str) -> str:
    return s.replace('[', '\\[')
