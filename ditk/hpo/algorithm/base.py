from typing import Callable, Type, Iterator


class BaseAlgorithm:
    def iter_config(self, vs) -> Iterator[object]:
        raise NotImplementedError  # pragma: no cover


class SearchRunner:
    def __init__(self, algo_cls: Type[BaseAlgorithm]):
        self.__config = {}
        self.__algo_cls = algo_cls

    def __getattr__(self, item) -> Callable[[object, ], 'SearchRunner']:
        def _get_config_value(v) -> SearchRunner:
            self.__config[item] = v
            return self

        return _get_config_value

    def _iter_config(self, vs):
        return self.__algo_cls(**self.__config).iter_config(vs)
