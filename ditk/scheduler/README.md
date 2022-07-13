# DI-toolkit: Scheduler

## Prerequisite

1, A runnable DI-engine reinforcement learning main file.

2, Kubenetes clusters access and installing kubectl tools. (For "k8s" mode only.)

3, A good yaml file for running job in Kubenetes. (For "k8s" mode only.)


## Quick Start for HPO running by Scheduler in Kubenetes

Here is a simple example.

To start, we need a normal DI-engine main file containing configurations.
In addition, at the end of the main file, a binary file, in which pickle dumps the return of hpo needs to be generated in the name of "./(dijob_project_name)-(id)/hpo/result". So that the return of DI-engine main function could be fetched. 

(For example: cartpole_dqn_config.py)
```python
from easydict import EasyDict

cartpole_dqn_config = dict(
    exp_name='cartpole_dqn_seed0',
    env=dict(
        collector_env_num=8,
        evaluator_env_num=5,
        n_evaluator_episode=5,
        stop_value=195,
        replay_path='cartpole_dqn_seed0/video',
    ),
    policy=dict(
        cuda=False,
        load_path=
        'cartpole_dqn_seed0/ckpt/ckpt_best.pth.tar',  # necessary for eval
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
    replay_buffer=dict(type='deque',
                       import_names=['ding.data.buffer.deque_buffer_wrapper']),
)
cartpole_dqn_create_config = EasyDict(cartpole_dqn_create_config)
create_config = cartpole_dqn_create_config

if __name__ == "__main__":
    # or you can enter `ding -m serial -c cartpole_dqn_config.py -s 0`
    from ding.entry import serial_pipeline
    serial_pipeline((main_config, create_config), seed=0)


```

After that, a yaml file template for k8s, of which the settings has to fit the k8s clusters and RL algo requirement, needs to be prepared. 

Here is an example of this yaml file template.

(cartpole_dijob_with_empty_configmap.yml)
```yaml
apiVersion: diengine.opendilab.org/v2alpha1
kind: DIJob
metadata:
  name: cartpole-dqn-hpo-k8s
spec:
  projectPath: /mnt/lustre/zhangjouwen.vendor/hpo/
  priority: "normal"  # 表示job的优先级，保留字段，调度中或许可以用到
  backoffLimit: 0  # 重启次数，可以为nil，表示无限重启；默认为3
  cleanPodPolicy: "Running"  # 表示job运行完成之后，如何处理worker pods
  preemptible: false  # 表示job是否允许被抢占，调度中对job资源改动之后涉及到抢占操作
  tasks:
  - replicas: 1
    type: none
    name: serial
    template:
      spec:
        containers:
        - name: di-container
          image: registry.sensetime.com/xlab/ding:cuda-nightly-atari
          imagePullPolicy: Always
          env:
          - name: PYTHONUNBUFFERED
            value: "1"
          resources:
            requests:
              # nvidia.com/gpu-a100: 1  # user-defined resource
              cpu: 2
              memory: "8Gi"
            limits:
              # nvidia.com/gpu-a100: 1
              cpu: 2
              memory: "8Gi"
          command: ["/bin/bash", "-c",]
          args:  # user-defined execution commands
          - |
            cat /etc/config/config.py
            export PATH=/opt/conda/bin:$PATH
            export http_proxy=http://proxy.sensetime.com:3128/
            export https_proxy=http://proxy.sensetime.com:3128/
            export HTTP_PROXY=http://proxy.sensetime.com:3128/
            export HTTPS_PROXY=http://proxy.sensetime.com:3128/
            pip config set global.index-url https://pkg.sensetime.com/repository/pypi-proxy/simple/
            pip config set install.trusted-host pypi.opencloud.sensetime.com
            python --version
            pip --version
            python -m pip install --upgrade pip
            cd /mnt/lustre/zhangjouwen.vendor/Github/opendilab/DI-engine-ditk
            pip install -e .
            pip install -U tensorboard
            cd /mnt/lustre/zhangjouwen.vendor/hpo/
            python /etc/config/config.py
            echo "Done!"
            sleep 150
          volumeMounts:
          - name: config-py
            mountPath: /etc/config
          - name: cache-volume
            mountPath: /dev/shm
          - name: data-volume
            mountPath: /mnt/cache/zhangjouwen.vendor
          - name: lustre-volume
            mountPath: /mnt/lustre/zhangjouwen.vendor
        volumes:
        - name: config-py
          configMap:
            name: config-py-
        - name: cache-volume
          emptyDir:
            medium: Memory
            sizeLimit: 128Mi
        - name: data-volume
          hostPath:
            path: /mnt/cache/zhangjouwen.vendor
        - name: lustre-volume
          hostPath:
            path: /mnt/lustre/zhangjouwen.vendor   
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-py-
data:
  config.py: |

```

Then, we could start the hpo algo and scheduler by few lines of python code.

```python
import os
from ditk import logging
from ditk.scheduler import run_scheduler
from ditk.hpo import R, randint, quniform, choice, uniform
from ditk.hpo import hpo


def demo():

    scheduler = run_scheduler_local(
        task_config_template_path=os.path.join(os.path.dirname(__file__), "../template/cartpole_dqn_config.py"),
        dijob_project_name="cartpole_dqn_hpo")

    hpo_info = {'policy': {'other': {'eps': {'start': uniform(0.5, 1)}}}}

    opt = hpo(scheduler.enable_hpo())
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

## Quick Start for HPO running by Scheduler locally

Just remove the k8s related configuration in "run_scheduler", and change the mode to "local".

## After launching scheduler-hpo

You will see the folloing output from terminal and get the status of every task.

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

## Notion

0, Hyper-parameter dict should be of the same dict format as that in your main file.

1, Adjust k8s yaml file content to fit your own account settings and volumes mount path.

2, Define a suitable name for the job in k8s. 

3, Define projectPath in yaml file, in which the hpo projects will be running. 
Match it with the folder directory to execute python in the k8s yaml file.
In my case, it is "/mnt/lustre/zhangjouwen.vendor/hpo/".

4, A pickled binary result file "/hpo/results" needs to be generated by your main file in the directory:

"(k8s_remote_project_path)/(dijob_project_name-id)/result.pkl"

5, Hpo algorithm minimize/maximize the same value name of the object that pickled in your result file "/result.pkl". 

(For example, if the pickled return is a dict-like object such as: {"value":200}, 

if you aim to maximize the "value", 

then you should "maximize(R['value'])" in hpo code.)

6, Be careful! If there is project of same name that has not been deleted in k8s cluster and remote mount volumes path, you have to clean them or choose a different project name.

7, Have fun!

## Contributing

We appreciate all contributions to improve `DI-toolkit`, both logic and system designs. Please refer to CONTRIBUTING.md for more guides.


## License

`DI-toolkit` released under the Apache 2.0 license.

