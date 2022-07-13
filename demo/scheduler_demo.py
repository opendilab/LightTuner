import os
from ditk import logging
from ditk.scheduler import run_scheduler, run_scheduler_local
from ditk.hpo import R, randint, quniform, choice, uniform
from ditk.hpo import hpo

if __name__ == "__main__":
    logging.try_init_root(logging.INFO)

    scheduler = run_scheduler_local(task_config_template_path=os.path.join(
        os.path.dirname(__file__), "../template/cartpole_dqn_config.py"),
                                    dijob_project_name="cartpole_dqn_hpo")

    hpo_info = {'policy': {'other': {'eps': {'start': uniform(0.5, 1)}}}}

    opt = hpo(scheduler.get_hpo_callable())
    cfg, ret, metrics = opt.grid() \
        .max_steps(5) \
        .max_workers(4) \
        .maximize(R['eval_value']) \
        .spaces(hpo_info).run()
    print(cfg)
    print(ret)

    scheduler.stop()
