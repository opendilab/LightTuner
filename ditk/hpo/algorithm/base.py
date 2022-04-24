from typing import Callable, Type, Iterator, Optional


class BaseAlgorithm:
    def __init__(self, max_steps: Optional[int], allow_unlimited_steps: bool = False):
        if not allow_unlimited_steps and max_steps is None:
            raise ValueError(f'Unlimited steps is not allowed in {repr(self.__class__)}.')
        self.__max_steps = max_steps

    @property
    def max_steps(self) -> Optional[int]:
        return self.__max_steps

    def iter_config(self, vs) -> Iterator[object]:
        raise NotImplementedError  # pragma: no cover


class SearchRunner:
    def __init__(self, algo_cls: Type[BaseAlgorithm], func):
        self.__config = {
            'max_steps': None,
        }
        self.__algo_cls = algo_cls
        self.__func = func

    def __getattr__(self, item) -> Callable[[object, ], 'SearchRunner']:
        def _get_config_value(v) -> SearchRunner:
            self.__config[item] = v
            return self

        return _get_config_value

    def max_steps(self, n: int) -> 'SearchRunner':
        self.__config['max_steps'] = n
        return self

    @property
    def _max_steps(self) -> Optional[int]:
        return self.__config['max_steps']

    def _iter_config(self, vs):
        return self.__algo_cls(**self.__config).iter_config(vs)

    def _ret_can_end(self, retval):
        return False

    def iter_func(self, vs):
        for step, cfg in enumerate(self._iter_config(vs), start=1):
            retval = self.__func(cfg)
            if self._max_steps is not None and step >= self._max_steps:
                return  # max step is reached
