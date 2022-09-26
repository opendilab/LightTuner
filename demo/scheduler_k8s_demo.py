import os

from ditk import logging

from lighttuner.hpo import R, uniform, choice
from lighttuner.hpo import hpo
from lighttuner.scheduler import run_scheduler_k8s


def demo():
    dir_name = os.path.abspath('./template')

    with run_scheduler_k8s(
            task_config_template_path=os.path.join(dir_name, "cartpole_dqn_config.py"),
            k8s_dijob_yaml_file_path=os.path.join(dir_name, "cartpole_dijob_with_empty_configmap.yml"),
    ) as scheduler:

        opt = hpo(scheduler.get_hpo_callable())
        cfg, ret, metrics = opt.grid() \
            .max_steps(5) \
            .max_workers(5) \
            .maximize(R['eval_value']) \
            .spaces({'policy': {'discount_factor': uniform(0.95, 1)}}).run()
        print(cfg)
        print(ret)


def didrive_demo():
    dir_name = os.path.abspath('./template')

    with run_scheduler_k8s(
            task_config_template_path=os.path.join(dir_name, "macro_ppo_config.py"),
            k8s_dijob_yaml_file_path=os.path.join(dir_name, "macro_dijob_with_empty_configmap.yml"),
    ) as scheduler:

        opt = hpo(scheduler.get_hpo_callable())
        cfg, ret, metrics = opt.grid() \
            .max_steps(5) \
            .max_workers(5) \
            .maximize(R['eval_value']) \
            .spaces({'policy': {'learn': {'learning_rate': uniform(1e-4, 5e-4)}}}).run()
        print(cfg)
        print(ret)


def tianshou_demo():
    dir_name = os.path.abspath('./template')

    with run_scheduler_k8s(
            task_config_template_path=os.path.join(dir_name, "tianshou_cartpole_dqn_config.py"),
            k8s_dijob_yaml_file_path=os.path.join(dir_name, "tianshou_dijob_with_empty_configmap.yml"),
    ) as scheduler:

        opt = hpo(scheduler.get_hpo_callable())
        cfg, ret, metrics = opt.grid() \
            .max_steps(3) \
            .max_workers(3) \
            .maximize(R['best_reward']) \
            .spaces({'policy': {'learning_rate': uniform(1e-3, 2e-3)}}).run()
        print(cfg)
        print(ret)


def d3rlpy_demo():
    dir_name = os.path.abspath('./template')

    with run_scheduler_k8s(
            task_config_template_path=os.path.join(dir_name, "d3rlpy_d4rl_halfcheetah_sac_config.py"),
            k8s_dijob_yaml_file_path=os.path.join(dir_name, "d3rlpy_d4rl_dijob_with_empty_configmap.yml"),
    ) as scheduler:

        hpo_info = {
            'env_id': choice(['halfcheetah-random-v0', 'halfcheetah-medium-v0', 'halfcheetah-expert-v0']),
            'seed': choice([0, 1, 2]),
        }

        opt = hpo(scheduler.get_hpo_callable())
        cfg, ret, metrics = opt.grid() \
            .max_steps(9) \
            .max_workers(1) \
            .maximize(R['rewards']) \
            .spaces(hpo_info).run()
        print(cfg)
        print(ret)


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    demo()
