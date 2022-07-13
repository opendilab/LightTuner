import os
from ditk import logging
from ditk.scheduler import run_scheduler_k8s
from ditk.hpo import R, choice, uniform
from ditk.hpo import hpo


def demo():

    scheduler = run_scheduler_k8s(
        task_config_template_path=os.path.join(os.path.dirname(__file__), "../template/cartpole_dqn_config.py"),
        k8s_dijob_yaml_file_path=os.path.join(os.path.dirname(__file__), "../template/cartpole_dijob_with_empty_configmap.yml"),
    )

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


def demo_lunarlander():

    scheduler = run_scheduler_k8s(
        task_config_template_path=os.path.join(os.path.dirname(__file__), "../template/lunarlander_dqn_config.py"),
        k8s_dijob_yaml_file_path=os.path.join(os.path.dirname(__file__), "../template/lunarlander_dijob_with_empty_configmap.yml"),
        time_out=2000)

    hpo_info = {
        'policy': {
            "learn": {
                "learning_rate": choice([5e-3, 1e-3, 5e-4])
            },
            "discount_factor": choice([0.995, 0.99, 0.985])
        }
    }

    opt = hpo(scheduler.get_hpo_callable())
    cfg, ret, metrics = opt.grid() \
        .max_steps(20) \
        .max_workers(7) \
        .maximize(R['eval_value']) \
        .spaces(hpo_info).run()
    print(cfg)
    print(ret)

    scheduler.stop()


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    demo()
