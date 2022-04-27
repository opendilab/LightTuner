import io
import time
from contextlib import redirect_stdout, redirect_stderr
from itertools import islice
from operator import __gt__, __lt__
from textwrap import dedent
from typing import Callable, Type, Optional, Tuple, Dict, Any

import inflection
from hbutils.collection import nested_walk
from hbutils.scale import time_to_delta_str
from hbutils.string import plural_word
from tabulate import tabulate

from .log import logger, escape
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
        self.__max_try = 3
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

    def max_retries(self, n: int) -> 'SearchRunner':
        if isinstance(n, int) and n >= 1:
            self.__max_try = n
            return self
        else:
            raise ValueError(f'Invalid max retry count - {repr(n)}.')

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
        """).strip())

        # initializing algorithm
        passback = ValueProxyLock()
        search_start_time = time.time()
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
                ======================= {inflection.ordinalize(cur_istep)} step =======================
                Step initialized, with variables - [bold bright_white on grey30]{rchain(cfg_display_values)}[/].
            """).strip())

            # run the function with several tries
            r_retval, r_err, r_time_cost = None, None, None
            for i in range(self.__max_try):
                # run the function once
                logger.info(f"Start the {inflection.ordinalize(i + 1)} running try of function {self.__func}...")
                cur_err = None
                with io.StringIO() as of, io.StringIO() as ef:
                    with redirect_stdout(of), redirect_stderr(ef):
                        _before_time = time.time()
                        try:
                            retval = self.__func(cur_cfg)
                        except BaseException as err:
                            cur_err = err
                        finally:
                            _after_time = time.time()
                    cur_stdout, cur_stderr = of.getvalue(), ef.getvalue()
                    r_time_cost = _after_time - _before_time

                # print the captured output
                if cur_stdout:
                    logger.info(dedent(f"""
    [blue]Stdout from function[/]:
    {escape(sblock(cur_stdout))}
                    """).strip())
                if cur_stderr:
                    logger.info(dedent(f"""
    [red]Stderr from function[/]:
    {escape(sblock(cur_stderr))}
                    """).strip())

                # check the error and result
                if cur_err is None:
                    r_err, r_retval = None, retval
                    break
                else:
                    r_err = cur_err
                    try_again_str = f'will try again later' if (i + 1) < self.__max_try \
                        else f'max retry limit is reached'
                    logger.info(dedent(f"""
                        [yellow]Error has occurred[/] - {escape(repr(r_err))}, {try_again_str} ({i + 1}/{self.__max_try})...
                    """).lstrip())

            can_break = False
            if r_err is None:
                # get full data
                metrics = {'time': r_time_cost}
                full_result = {'return': r_retval, 'metrics': metrics}

                # show result information
                res_display_values = [
                    (self.__target_name, self._get_result_value(full_result)),
                    *((name, getter(full_result)) for name, getter in self.__rank_concerns)
                ]
                logger.info(dedent(f"""
                    Function running [green]completed[/], time cost: {"%.3f" % r_time_cost} seconds,
                    with concerned results - [bold bright_white on grey30]{rchain(res_display_values)}[/].
                """).strip())

                # maintain the ranklist
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

                # condition check
                if self._is_result_okay(full_result):
                    can_break = True

            else:
                # log the exception
                try:
                    raise r_err
                except:
                    logger.exception(f'Function running [red]failed[/], '
                                     f'time cost: {"%.3f" % r_time_cost} seconds, '
                                     f'this step will be skipped and ignored due to this failure.')
                passback.fail(r_err)

            # print ranklist and running duration
            logger.info(dedent(f"""
Current ranklist ({plural_word(self.__rank_capacity, 'best record')} will be shown):
{escape(self._make_rank_table(indeps, ranklist))}
            """).strip())
            logger.info(dedent(f"""
                This search task has been lasted for {time_to_delta_str(time.time() - search_start_time)}.

            """).lstrip())

            # condition check
            if can_break:
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
