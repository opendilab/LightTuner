import os

from ditk import logging

from lighttuner.hpo import R, uniform
from lighttuner.hpo import hpo
from lighttuner.scheduler import run_scheduler_k8s


def demo():
    dirname = os.path.abspath('./template')

    scheduler = run_scheduler_k8s(
        task_config_template_path=os.path.join(dirname, "cartpole_dqn_config.py"),
        k8s_dijob_yaml_file_path=os.path.join(dirname, "cartpole_dijob_with_empty_configmap.yml"),
    )

    hpo_info = {'policy': {'discount_factor': uniform(0.95, 1)}}

    opt = hpo(scheduler.get_hpo_callable())
    cfg, ret, metrics = opt.grid() \
        .max_steps(5) \
        .max_workers(5) \
        .maximize(R['eval_value']) \
        .spaces(hpo_info).run()
    print(cfg)
    print(ret)

    scheduler.stop()


def didrive_demo():
    dirname = os.path.abspath('./template')

    scheduler = run_scheduler_k8s(
        task_config_template_path=os.path.join(dirname, "macro_ppo_config.py"),
        k8s_dijob_yaml_file_path=os.path.join(dirname, "macro_dijob_with_empty_configmap.yml"),
    )

    hpo_info = {'policy': {'learn': {'learning_rate': uniform(1e-4, 5e-4)}}}

    opt = hpo(scheduler.get_hpo_callable())
    cfg, ret, metrics = opt.grid() \
        .max_steps(5) \
        .max_workers(5) \
        .maximize(R['eval_value']) \
        .spaces(hpo_info).run()
    print(cfg)
    print(ret)

    scheduler.stop()


def tianshou_demo():
    dirname = os.path.abspath('./template')

    scheduler = run_scheduler_k8s(
        task_config_template_path=os.path.join(dirname, "tianshou_cartpole_dqn_config.py"),
        k8s_dijob_yaml_file_path=os.path.join(dirname, "tianshou_dijob_with_empty_configmap.yml"),
    )

    hpo_info = {'policy': {'learning_rate': uniform(1e-3, 2e-3)}}

    opt = hpo(scheduler.get_hpo_callable())
    cfg, ret, metrics = opt.grid() \
        .max_steps(3) \
        .max_workers(3) \
        .maximize(R['best_reward']) \
        .spaces(hpo_info).run()
    print(cfg)
    print(ret)

    scheduler.stop()


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    demo()
