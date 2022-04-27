import io
import time
from contextlib import redirect_stdout, redirect_stderr
from itertools import islice
from operator import __gt__, __lt__
from textwrap import dedent
from typing import Callable, Type, Optional, Tuple, Dict, Any

import inflection
from hbutils.collection import nested_walk
from hbutils.string import plural_word
from tabulate import tabulate

from .log import logger
from .result import R as _OR
from .result import _to_model
from ..algorithm import BaseAlgorithm
from ..utils import ValueProxyLock, sblock, rchain
from ..value import HyperValue

R = _OR['return']
M = _OR['metrics']


def _find_hv(vs):
    for path, obj in nested_walk(vs):
        if isinstance(obj, HyperValue):
            r = _OR
            for pitem in path:
                r = r[pitem]
            yield path, r


class SearchRunner:
    def __init__(self, algo_cls: Type[BaseAlgorithm], func):
        self.__func = func
        self.__config: Dict[str, object] = {
            'max_steps': None,
            'opt_direction': None,
        }
        self.__algorithm_cls = algo_cls  # algorithm class
        self.__stop_condition = None  # end condition, determine when to stop
        self.__order_condition = None  # order condition, determine which is the best
        self.__target_name = 'target'
        self.__rank_capacity = 5  # rank list capacity
        self.__rank_concerns = []
        self.__spaces = None  # space for searching

    def __getattr__(self, item) -> Callable[[object, ], 'SearchRunner']:
        def _get_config_value(v) -> SearchRunner:
            self.__config[item] = v
            return self

        return _get_config_value

    def max_steps(self, n: int) -> 'SearchRunner':
        self.__config['max_steps'] = n
        return self

    def stop_when(self, condition) -> 'SearchRunner':
        if self.__stop_condition is None:
            self.__stop_condition = _to_model(condition)
        else:
            self.__stop_condition = self.__stop_condition | _to_model(condition)

        return self

    def maximize(self, condition, name='target') -> 'SearchRunner':
        if self.__order_condition is None:
            self.__order_condition = (_to_model(condition), __gt__)
            self.__config['opt_direction'] = 'maximize'
            self.__target_name = name
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    def minimize(self, condition, name='target') -> 'SearchRunner':
        if self.__order_condition is None:
            self.__order_condition = (_to_model(condition), __lt__)
            self.__config['opt_direction'] = 'minimize'
            self.__target_name = name
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    def rank(self, n) -> 'SearchRunner':
        if n >= 1:
            self.__rank_capacity = n
            return self
        else:
            raise ValueError(f'Invalid rank list capacity - {repr(n)}.')

    def concern(self, cond, name):
        self.__rank_concerns.append((name, cond))
        return self

    @property
    def _max_steps(self) -> Optional[int]:
        # noinspection PyTypeChecker
        return self.__config['max_steps']

    def _is_result_okay(self, retval):
        if self.__stop_condition is not None:
            return not not self.__stop_condition(retval)
        else:
            return False

    def spaces(self, vs) -> 'SearchRunner':
        self.__spaces = vs
        return self

    def _is_result_better(self, origin, newres):
        if self.__order_condition is not None:
            cond, cmp = self.__order_condition
            return cmp(cond(newres), cond(origin))
        else:
            return True

    def _get_result_value(self, res):
        if self.__order_condition is not None:
            conf, _ = self.__order_condition
            return conf(res)
        else:
            return R(res)

    def _make_rank_table(self, indeps, ranklist):
        return tabulate(
            [
                [
                    istep,
                    *(getter(cfg) for _, getter in indeps),
                    self._get_result_value(fres),
                    *(getter(fres) for _, getter in self.__rank_concerns),
                ] for istep, cfg, fres in ranklist],
            headers=[
                '#',
                *(name for name, _ in indeps),
                self.__target_name,
                *(name for name, _ in self.__rank_concerns)
            ], tablefmt='psql'
        )

    def run(self) -> Optional[Tuple[Any, Any, Any]]:
        # algorithm information
        logger.info(dedent(f"""
            {self.__algorithm_cls.algorithm_name().capitalize()} will be used, with [bold bright_white on grey30]{
        rchain(sorted((name, val) for name, val in self.__config.items()))}[/]
        """).strip(), extra={'markup': True})

        # initializing algorithm
        passback = ValueProxyLock()
        cfg_iter = self.__algorithm_cls(**self.__config).iter_config(self.__spaces, passback)
        indeps = [('.'.join(map(str, pname)), getter) for pname, getter in _find_hv(self.__spaces)]
        if self._max_steps is not None:
            cfg_iter = islice(cfg_iter, self._max_steps)
        logger.info(f'{self.__algorithm_cls.algorithm_name()} initialized.'.capitalize())

        # run the search
        ranklist, break_by_stop = [], False
        for cur_istep, cur_cfg in enumerate(cfg_iter, start=1):
            # shown input config
            cfg_display_values = [(name, getter(cur_cfg)) for name, getter in indeps]
            logger.info(dedent(f"""
                The {inflection.ordinalize(cur_istep)} step initialized, with [bold bright_white on grey30]{rchain(cfg_display_values)}[/]
                Start running the {inflection.ordinalize(cur_istep)} step...
            """).strip(), extra={"markup": True})

            # run the function
            with io.StringIO() as of, io.StringIO() as ef:
                with redirect_stdout(of), redirect_stderr(ef):
                    _before_time = time.time()
                    retval = self.__func(cur_cfg)
                    _after_time = time.time()
                cur_stdout, cur_stderr = of.getvalue(), ef.getvalue()

            # print the captured output
            if cur_stdout:
                logger.info(dedent(f"""
Stdout of function {self.__func}:
{sblock(cur_stdout)}
                """).strip())
            if cur_stderr:
                logger.info(dedent(f"""
Stderr of function {self.__func}:
{sblock(cur_stderr)}
                """).strip())

            # get full data
            cur_duration = _after_time - _before_time
            metrics = {
                'time': cur_duration,
            }
            full_result = {'return': retval, 'metrics': metrics}

            # show result information
            res_display_values = [
                (self.__target_name, self._get_result_value(full_result)),
                *((name, getter(full_result)) for name, getter in self.__rank_concerns)
            ]
            logger.info(dedent(f"""
                The {inflection.ordinalize(cur_istep)} step completed, time cost: {"%.3f" % cur_duration} seconds,
                with [bold bright_white on grey30]{rchain(res_display_values)}[/]
            """).strip(), extra={'markup': True})

            # maintain and show the ranklist table
            passback.put(self._get_result_value(full_result))
            ins_pos = None
            for i, (_, _, fres) in enumerate(ranklist):
                if self._is_result_better(fres, full_result):
                    ins_pos = i
                    break
            if ins_pos is None:
                ranklist.append((cur_istep, cur_cfg, full_result))
            else:
                ranklist = ranklist[:ins_pos] + [(cur_istep, cur_cfg, full_result)] + ranklist[ins_pos:]
            ranklist = ranklist[:self.__rank_capacity]
            logger.info(dedent(f"""
Current ranklist ({plural_word(self.__rank_capacity, 'record')} will be shown):
{self._make_rank_table(indeps, ranklist)}
            """).lstrip())

            # condition check
            if self._is_result_okay(full_result):
                break_by_stop = True
                break

        # ending information
        if break_by_stop:
            logger.info('Stop condition is meet, search will be ended...')
        else:
            logger.info('Iteration is over, search will be ended...')

        # return
        if ranklist:
            final_step, final_cfg, final_result = ranklist[0]
            final_return, final_metrics = final_result['return'], final_result['metrics']
            return final_cfg, final_return, final_metrics  # max step is reached
        else:
            return None
