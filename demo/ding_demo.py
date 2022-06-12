import copy
import os

import gym
import numpy as np
from ding.config import compile_config
from ding.envs import BaseEnvManager, DingEnvWrapper
from ding.model import DQN
from ding.policy import DQNPolicy
from ding.rl_utils import get_epsilon_greedy_fn
from ding.utils import set_pkg_seed
from ding.worker import BaseLearner, SampleSerialCollector, InteractionSerialEvaluator, AdvancedReplayBuffer
from dizoo.classic_control.cartpole.config.cartpole_dqn_config import cartpole_dqn_config
from easydict import EasyDict
from tensorboardX import SummaryWriter

from ditk import logging
from ditk.hpo import hpo, R, randint, M, uniform


# Get DI-engine form env class
def wrapped_cartpole_env():
    return DingEnvWrapper(
        gym.make('CartPole-v0'),
        EasyDict(env_wrapper='default'),
    )


@hpo
def main(v):
    seed = 0
    cfg = copy.deepcopy(cartpole_dqn_config)
    cfg.seed = seed
    cfg.policy.learn.learning_rate = v['learning_rate']
    cfg.policy.nstep = v['nstep']
    cfg.exp_name = cfg.exp_name + '_lr{}_nstep{}'.format(v['learning_rate'], v['nstep'])

    cfg = compile_config(
        cfg,
        BaseEnvManager,
        DQNPolicy,
        BaseLearner,
        SampleSerialCollector,
        InteractionSerialEvaluator,
        AdvancedReplayBuffer,
        save_cfg=True
    )
    collector_env_num, evaluator_env_num = cfg.env.collector_env_num, cfg.env.evaluator_env_num
    collector_env = BaseEnvManager(env_fn=[wrapped_cartpole_env for _ in range(collector_env_num)], cfg=cfg.env.manager)
    evaluator_env = BaseEnvManager(env_fn=[wrapped_cartpole_env for _ in range(evaluator_env_num)], cfg=cfg.env.manager)

    # Set random seed for all package and instance
    collector_env.seed(seed)
    evaluator_env.seed(seed, dynamic_seed=False)
    set_pkg_seed(seed, use_cuda=cfg.policy.cuda)

    # Set up RL Policy
    model = DQN(**cfg.policy.model)
    policy = DQNPolicy(cfg.policy, model=model)

    # Set up collection, training and evaluation utilities
    tb_logger = SummaryWriter(os.path.join('./{}/log/'.format(cfg.exp_name), 'serial'))
    learner = BaseLearner(cfg.policy.learn.learner, policy.learn_mode, tb_logger, exp_name=cfg.exp_name)
    collector = SampleSerialCollector(
        cfg.policy.collect.collector, collector_env, policy.collect_mode, tb_logger, exp_name=cfg.exp_name
    )
    evaluator = InteractionSerialEvaluator(
        cfg.policy.eval.evaluator, evaluator_env, policy.eval_mode, tb_logger, exp_name=cfg.exp_name
    )
    replay_buffer = AdvancedReplayBuffer(cfg.policy.other.replay_buffer, tb_logger, exp_name=cfg.exp_name)

    # Set up other modules, etc. epsilon greedy
    eps_cfg = cfg.policy.other.eps
    epsilon_greedy = get_epsilon_greedy_fn(eps_cfg.start, eps_cfg.end, eps_cfg.decay, eps_cfg.type)

    # Training & Evaluation loop
    while True:
        # Evaluating at the beginning and with specific frequency
        if evaluator.should_eval(learner.train_iter):
            stop, eval_info = evaluator.eval(learner.save_checkpoint, learner.train_iter, collector.envstep)
            if stop:
                break
        # Update other modules
        eps = epsilon_greedy(collector.envstep)
        # Sampling data from environments
        new_data = collector.collect(train_iter=learner.train_iter, policy_kwargs={'eps': eps})
        replay_buffer.push(new_data, cur_collector_envstep=collector.envstep)
        # Training
        for i in range(cfg.policy.learn.update_per_collect):
            train_data = replay_buffer.sample(learner.policy.get_attribute('batch_size'), learner.train_iter)
            if train_data is None:
                break
            learner.train(train_data, collector.envstep)
    return {
        'envstep': collector.envstep,
        'train_iter': learner.train_iter,
        'reward': np.mean([v['final_eval_reward'].item() for v in eval_info])
    }


if __name__ == "__main__":
    logging.try_init_root(logging.INFO)
    print(main.bayes()
          .max_steps(20)
          .seed(0)
          .minimize(R['envstep'], 'envstep')
          .concern(R['reward'], 'reward')
          .concern(M['time'], 'time_cost')
          .spaces(
        {
            'learning_rate': 10 ** uniform(-4, -2),
            'nstep': randint(1, 5)
        }
    ).run())
