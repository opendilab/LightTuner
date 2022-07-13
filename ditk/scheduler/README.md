# DI-toolkit: Scheduler

## Prerequisite

1. A runnable entry (main program) file with modified config field, such as DI-engine RL config file.

2. Kubenetes clusters access and installing kubectl tools. (For "k8s" mode only.)

3. A good yaml file for running job in Kubenetes. (For "k8s" mode only.)


## Quick Start for HPO Launched by Scheduler in Local and Kubenetes

Here is a simple example:

To start, we need a entry file containing configurations, we use DI-engine RL config as example ([Link](https://gitlab.bj.sensetime.com/open-XLab/cell/di-toolkit/-/blob/main/ditk/template/cartpole_dqn_config.py)):

In addition, we should save a binary file named ``<dijob_project_name-id>/hpo/result.pkl`` at the end of the main file, which contains necessary metrics like accuracy, mAP, discount returns and so on.


After that, we beign to run the first demo  (all the following codes are located in ``di-toolkit/demo`` directory). 

If you want to run hpo with scheduler in your local machine, you can use the following codes:
```python
import os
import ditk
from ditk import logging
from ditk.scheduler import run_scheduler_local
from ditk.hpo import R, uniform
from ditk.hpo import hpo


def demo():
    dirname = os.path.join(ditk.__path__[0], 'template')

    scheduler = run_scheduler_local(
        task_config_template_path=os.path.join(dirname, "cartpole_dqn_config.py"),
        dijob_project_name="cartpole_dqn_hpo"
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
```

If you want to run it in K8s, a k8s yaml file template is necessary, of which the settings has to fit the k8s clusters and RL algo requirement, needs to be prepared. 

[Here](https://gitlab.bj.sensetime.com/open-XLab/cell/di-toolkit/-/blob/main/ditk/template/cartpole_dijob_with_empty_configmap.yml) is an template, you can modify it according to your demands.

Then, we could start the hpo algo and scheduler by few lines of python code.

```python
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

1, Adjust k8s yaml file content to fit your own setting
- ``basePath (volumes mount path)``
- ``projectPath``, which the hpo projects will be running and output results
- ``metadata.name``, which will be used to generate the identifier for the job in k8s.
- computational resource, such as GPU, CPU and memory
- args, which installs user-defined packages

2, Hpo algorithm minimize/maximize the same value name of the object that pickled in your result file ``result.pkl``. 

- For example, if the pickled return is a dict-like object such as: {"value": 200}, if you aim to maximize the "value", then you should "maximize(R['value'])" in hpo code.

3, Have fun!
