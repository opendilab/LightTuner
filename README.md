# DI-toolkit


[![pipeline status](https://gitlab.bj.sensetime.com/open-XLab/cell/di-toolkit/badges/main/pipeline.svg)](https://gitlab.bj.sensetime.com/open-XLab/cell/di-toolkit/-/commits/main)
[![coverage report](https://gitlab.bj.sensetime.com/open-XLab/cell/di-toolkit/badges/main/coverage.svg)](https://gitlab.bj.sensetime.com/open-XLab/cell/di-toolkit/-/commits/main)

A simple toolkit packages:
  - logger
  - hpo: automatic hyper-parameter tuning
  - scheduler: automatic task resource scheduler


## Installation

You can simply install it with `pip` command line from the official PyPI site.

```shell
pip install DI-toolkit
```

Or install from latest source code as follows:
```shell
git clone https://gitlab.bj.sensetime.com/open-XLab/cell/di-toolkit.git
cd di-toolkit
pip install . --user
```

## Quick Start for HPO

Here is a simple example:

```python
import random
import time

from ditk import logging
from ditk.hpo import hpo, R, M, uniform, randint


@hpo
def opt_func(v):  # this function is still usable after decorating
    x, y = v['x'], v['y']
    time.sleep(5.0)
    logging.info(f"This time's config: {v!r}")  # log will be captured
    if random.random() < 0.5:  # randomly raise exception
        raise ValueError('Fxxk this shxt')  # retry is supported

    return {
        'result': x * y,
        'sum': x + y,
    }


if __name__ == '__main__':
    logging.try_init_root(logging.DEBUG)
    print(opt_func.bayes()  # random algorithm
          .max_steps(50)  # max steps
          .minimize(R['result'])  # the maximize/minimize target you need to optimize,
          .concern(M['time'], 'time_cost')  # extra concerned values (from metrics)
          .concern(R['sum'], 'sum')  # extra concerned values (from return value of function)
          .stop_when(R['result'] <= -800)  # conditional stop is supported
          .spaces(  # search spaces
        {
            'x': uniform(-10, 110),  # continuous space
            'y': randint(-10, 20),  # integer based space
            'z': {
                # 't': choice(['a', 'b', 'c', 'd', 'e']),  # enumerate space
                't': uniform(0, 10),  # enumerate space is not supported in bayesian optimization
            },
        }
    ).run())

```

This optimization progress is parallel, which has n (number of cpus) workers in default. If you need to customize the count of workers, just use `max_workers(n)` method.

## Quick Start for Scheduler
You can refer to `ditk/scheduler/README.md` for more details.

## Contributing

We appreciate all contributions to improve `DI-toolkit`, both logic and system designs. Please refer to CONTRIBUTING.md for more guides.


## License

`DI-toolkit` released under the Apache 2.0 license.
