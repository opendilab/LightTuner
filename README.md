# LightTuner

[![PyPI](https://img.shields.io/pypi/v/lighttuner)](https://pypi.org/project/lighttuner/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/lighttuner)
![Loc](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/HansBug/cfbcfc91f1353f1d4b2607c433d46bd6/raw/loc.json)
![Comments](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/HansBug/cfbcfc91f1353f1d4b2607c433d46bd6/raw/comments.json)

[![Docs Deploy](https://github.com/opendilab/LightTuner/workflows/Docs%20Deploy/badge.svg)](https://github.com/opendilab/LightTuner/actions?query=workflow%3A%22Docs+Deploy%22)
[![Code Test](https://github.com/opendilab/LightTuner/workflows/Code%20Test/badge.svg)](https://github.com/opendilab/LightTuner/actions?query=workflow%3A%22Code+Test%22)
[![Badge Creation](https://github.com/opendilab/LightTuner/workflows/Badge%20Creation/badge.svg)](https://github.com/opendilab/LightTuner/actions?query=workflow%3A%22Badge+Creation%22)
[![Package Release](https://github.com/opendilab/LightTuner/workflows/Package%20Release/badge.svg)](https://github.com/opendilab/LightTuner/actions?query=workflow%3A%22Package+Release%22)
[![codecov](https://codecov.io/gh/opendilab/LightTuner/branch/main/graph/badge.svg?token=XJVDP4EFAT)](https://codecov.io/gh/opendilab/LightTuner)

[![GitHub stars](https://img.shields.io/github/stars/opendilab/LightTuner)](https://github.com/opendilab/LightTuner/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/opendilab/LightTuner)](https://github.com/opendilab/LightTuner/network)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/opendilab/LightTuner)
[![GitHub issues](https://img.shields.io/github/issues/opendilab/LightTuner)](https://github.com/opendilab/LightTuner/issues)
[![GitHub pulls](https://img.shields.io/github/issues-pr/opendilab/LightTuner)](https://github.com/opendilab/LightTuner/pulls)
[![Contributors](https://img.shields.io/github/contributors/opendilab/LightTuner)](https://github.com/opendilab/LightTuner/graphs/contributors)
[![GitHub license](https://img.shields.io/github/license/opendilab/LightTuner)](https://github.com/opendilab/LightTuner/blob/master/LICENSE)

A simple hyper-parameter optimization toolkit:

- hpo: automatic hyper-parameter tuning
- scheduler: automatic task resource scheduler

## Installation

You can simply install it with `pip` command line from the official PyPI site.

```shell
pip install lighttuner
```

Or install from latest source code as follows:

```shell
git clone https://github.com/opendilab/LightTuner.git
cd LightTuner
pip install . --user
```

## Quick Start for HPO

Here is a simple example:

```python
import random
import time

from ditk import logging

from lighttuner.hpo import hpo, R, M, uniform, randint


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

This optimization progress is parallel, which has n (number of cpus) workers in default. If you need to customize the
count of workers, just use `max_workers(n)` method.

## Quick Start for Scheduler

You can refer to `lighttuner/scheduler/README.md` for more details.

## Contributing

We appreciate all contributions to improve `LightTuner`, both logic and system designs. Please refer to CONTRIBUTING.md
for more guides.

## License

`LightTuner` released under the Apache 2.0 license.
