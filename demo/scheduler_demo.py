import os
from ditk import logging
from ditk.scheduler import run_scheduler_local
from ditk.hpo import R, uniform
from ditk.hpo import hpo


def demo():

    scheduler = run_scheduler_local(
        task_config_template_path=os.path.join(os.path.dirname(__file__), "../template/cartpole_dqn_config.py"),
        dijob_project_name="cartpole_dqn_hpo")

    hpo_info = {'policy': {'discount_factor':  uniform(0.95, 1)}}

    opt = hpo(scheduler.get_hpo_callable())
    cfg, ret, metrics = opt.grid() \
        .max_steps(5) \
        .max_workers(4) \
        .maximize(R['eval_value']) \
        .spaces(hpo_info).run()
    print(cfg)
    print(ret)

    scheduler.stop()


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    demo()
