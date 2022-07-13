# DI-toolkit: Scheduler

## Prerequisite

1. A runnable entry (main program) file with modified config field, such as DI-engine RL config file.

2. Kubenetes clusters access and installing kubectl tools. (For "k8s" mode only.)

3. A good yaml file for running job in Kubenetes. (For "k8s" mode only.)


## Quick Start for HPO Launched by Scheduler in Local and Kubenetes

Here is a simple example:

To start, we need a entry file containing configurations, we use DI-engine RL config as example ([Link](https://github.com/opendilab/DI-engine/blob/main/dizoo/classic_control/cartpole/config/cartpole_dqn_config.py)):
```python
from easydict import EasyDict

cartpole_dqn_config = dict(
    exp_name='cartpole_dqn_seed0',
    env=dict(
        collector_env_num=8,
        evaluator_env_num=5,
        n_evaluator_episode=5,
        stop_value=195,
    ),
    policy=dict(
        cuda=True,
        model=dict(
            obs_shape=4,
            action_shape=2,
            encoder_hidden_size_list=[128, 128, 64],
            dueling=True,
        ),
        nstep=1,
        discount_factor=0.97,
        learn=dict(
            batch_size=64,
            learning_rate=0.001,
        ),
        collect=dict(n_sample=8),
        eval=dict(evaluator=dict(eval_freq=40, )),
        other=dict(
            eps=dict(
                type='exp',
                start=0.95,
                end=0.1,
                decay=10000,
            ),
            replay_buffer=dict(replay_buffer_size=20000, ),
        ),
    ),
)
cartpole_dqn_config = EasyDict(cartpole_dqn_config)
main_config = cartpole_dqn_config
cartpole_dqn_create_config = dict(
    env=dict(
        type='cartpole',
        import_names=['dizoo.classic_control.cartpole.envs.cartpole_env'],
    ),
    env_manager=dict(type='base'),
    policy=dict(type='dqn'),
)
cartpole_dqn_create_config = EasyDict(cartpole_dqn_create_config)
create_config = cartpole_dqn_create_config

if __name__ == "__main__":
    from ding.entry import serial_pipeline
    serial_pipeline((main_config, create_config), seed=0)  # save result.pkl by default
```
In addition, we should save a binary file named ``<dijob_project_name-id>/hpo/result.pkl`` at the end of the main file, which contains necessary metrics like accuracy, mAP, discount returns and so on.


After that, we beign to run the first demo  (all the following codes are located in ``di-toolkit/demo`` directory). 

If you want to run hpo with scheduler in your local machine, you can use the following codes:
```python
import os
from ditk import logging
from ditk.scheduler import run_scheduler_local
from ditk.hpo import R, randint, quniform, choice, uniform
from ditk.hpo import hpo


def demo():

    scheduler = run_scheduler_local(
        task_config_template_path=os.path.join(os.path.dirname(__file__), "../template/cartpole_dqn_config.py"),
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


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    demo()
```

If you want to run it in K8s, a k8s yaml file template is necessary, of which the settings has to fit the k8s clusters and RL algo requirement, needs to be prepared. 

[Here](https://gitlab.bj.sensetime.com/open-XLab/cell/di-toolkit/-/blob/main/template/cartpole_dijob_with_empty_configmap.yml) is an template, you can modify it according to your demands.

Then, we could start the hpo algo and scheduler by few lines of python code.

```python
import os
from ditk import logging
from ditk.scheduler import run_scheduler_k8s
from ditk.hpo import R, randint, quniform, choice, uniform
from ditk.hpo import hpo


def demo():

    scheduler = run_scheduler_k8s(
        task_config_template_path=os.path.join(os.path.dirname(__file__), "../template/cartpole_dqn_config.py"),
        k8s_dijob_yaml_file_path=os.path.join(os.path.dirname(__file__), "../template/cartpole_dijob_with_empty_configmap.yml"),
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


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    demo()
```


After launching scheduler successfully, you will see the following output from terminal and get the status of every task.

```text

 +---------------+----------------------------------------+ 
 | status        | instances                              |
 +===============+========================================+
 | task_defined  | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] |
 +---------------+----------------------------------------+
 | task_running  | [8]                                    |
 +---------------+----------------------------------------+
 | task_waiting  | [9, 10, 11]                            |
 +---------------+----------------------------------------+
 | task_finished | [0, 1, 2, 3, 4, 5, 6, 7]               |
 +---------------+----------------------------------------+
 | task_success  | [1, 3, 4, 5, 6, 7]                     |
 +---------------+----------------------------------------+
 | task_abnormal | [0, 2]                                 |
 +---------------+----------------------------------------+


```

## Tips

0, Hyper-parameter dict should be of the same dict structure format as that in your main file.

1, Adjust k8s yaml file content to fit your own args, resource and volumes mount path.

2, Specify ``metadata.name`` in DIJob, which will be used to generate the identifier for the job in k8s.

3, Specify ``metadata.projectPath`` field in yaml file, in which the hpo projects will be running.

4, Hpo algorithm minimize/maximize the same value name of the object that pickled in your result file ``result.pkl``. 

- For example, if the pickled return is a dict-like object such as: {"value": 200}, if you aim to maximize the "value", then you should "maximize(R['value'])" in hpo code.

5, Have fun!
