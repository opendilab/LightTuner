import os

from ditk import logging

from lighttuner.hpo import R, uniform, choice
from lighttuner.hpo import hpo
from lighttuner.scheduler import run_scheduler_local

import wandb
project_name = "sweeps-scheduler-1"
sweep_config = {'method': 'random'}
metric = {'name': 'eval_value', 'goal': 'minimize'}
sweep_config['metric'] = metric
parameters_dict = {
    'seed': {
        'values': [0, 1, 2],
    },
    'learning_rate': {
        'values': [0.001, 0.002],
    },
}
sweep_config['parameters'] = parameters_dict
parameters_dict.update({'epochs': {'value': 1}})
parameters_dict.update(
    {
        'discount_factor': {
            # a flat distribution between 0 and 0.1
            'distribution': 'uniform',
            'min': 0.95,
            'max': 1
        },
    }
)
import pprint
pprint.pprint(sweep_config)


def run_sweep(username):
    sweep_id = wandb.sweep(sweep_config, project=project_name)
    sweep_id = username + "/" + project_name + "/" + sweep_id
    return sweep_id


def sweep_demo():
    username = "zjowowen"
    sweep_id = run_sweep(username)

    dir_name = os.path.abspath('./template')

    with run_scheduler_local(task_config_template_path=os.path.join(dir_name, "cartpole_dqn_config.py"),
                             dijob_project_name="cartpole_dqn_hpo") as scheduler:

        def train(config=None):
            # Initialize a new wandb run
            with wandb.init(config=config):
                # If called by wandb.agent, as below,
                # this config will be set by Sweep Controller
                config = wandb.config
                new_config = {
                    'policy': {
                        'learn': {
                            'learning_rate': config['learning_rate']
                        },
                        'discount_factor': config['discount_factor'],
                    },
                }

                return_dict = scheduler.get_hpo_callable()(new_config, 1)

                for epoch in range(config.epochs):
                    wandb.log({"eval_value": return_dict["eval_value"], "epoch": epoch})

        wandb.agent(sweep_id, train, count=5)


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    sweep_demo()
