import os

from ditk import logging

from lighttuner.hpo import R, uniform
from lighttuner.hpo import hpo
from lighttuner.scheduler import run_scheduler_local


def demo():
    dirname = os.path.abspath('./template')

    scheduler = run_scheduler_local(
        task_config_template_path=os.path.join(dirname, "cartpole_dqn_config.py"),
        dijob_project_name="cartpole_dqn_hpo"
    )

    hpo_info = {'policy': {'discount_factor': uniform(0.95, 1)}}

    opt = hpo(scheduler.get_hpo_callable())
    cfg, ret, metrics = opt.grid() \
        .max_steps(5) \
        .max_workers(4) \
        .maximize(R['eval_value']) \
        .spaces(hpo_info).run()
    print(cfg)
    print(ret)

    scheduler.stop()


def didrive_demo():
    dirname = os.path.abspath('./template')

    scheduler = run_scheduler_local(
        task_config_template_path=os.path.join(dirname, "macro_ppo_config.py"),
        max_number_of_running_task=1,
        dijob_project_name="macro_ppo_hpo"
    )

    hpo_info = {'policy': {'learn': {'learning_rate': uniform(1e-4, 5e-4)}}}

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
