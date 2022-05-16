import random
import time

from ditk import logging
from ditk.hpo import hpo, R, M, choice, uniform, randint


@hpo
def opt_func(v):  # this function is still usable after decorating
    x, y = v['x'], v['y']
    time.sleep(0.1)
    logging.info(f"This [u]time's[/] config: {v}")  # stdout will be captured
    logging.warning("This is print line in stderr")  # stderr will be captured
    if random.random() < 0.5:  # randomly raise exception
        raise ValueError('Fxxk this shxt')  # retry is supported

    return {
        'result': x * y,
        'sum': x + y,
    }


if __name__ == '__main__':
    logging.try_init_root(logging.INFO)
    print(opt_func.random()  # random algorithm
          .max_steps(30)  # max steps
          .minimize(R['result'])  # the maximize/minimize target you need to optimize,
          .concern(M['time'], 'time_cost')  # extra concerned values (from metrics)
          .concern(R['sum'], 'sum')  # extra concerned values (from return value of function)
          .stop_when(R['result'] <= -800)  # conditional stop is supported
          .spaces(  # search spaces
        {
            'x': uniform(-10, 110),  # continuous space
            'y': randint(-10, 20),  # integer based space
            'z': {
                't': choice(['a', 'b', 'c', 'd', 'e']),  # enumerate space
            },
        }
    ).run())
