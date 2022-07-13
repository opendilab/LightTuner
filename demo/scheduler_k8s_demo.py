import os
import ditk
from ditk import logging
from ditk.scheduler import run_scheduler_k8s
from ditk.hpo import R, uniform
from ditk.hpo import hpo


def demo():
    dirname = os.path.join(ditk.__path__[0], 'template')

    scheduler = run_scheduler_k8s(
        task_config_template_path=os.path.join(dirname, "cartpole_dqn_config.py"),
        k8s_dijob_yaml_file_path=os.path.join(dirname, "cartpole_dijob_with_empty_configmap.yml"),
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


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    demo()
