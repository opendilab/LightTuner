import gym
import tianshou as ts
import torch, numpy as np
from torch import nn
from easydict import EasyDict

main_config = dict(exp_name='tianshou_cartpole_dqn_seed0',
                   env=dict(env_id='CartPole-v0', ),
                   policy=dict(learn=dict(
                       learning_rate=1e-3,
                       batch_size=64,
                   ), ))
main_config = EasyDict(main_config)


class Net(nn.Module):

    def __init__(self, state_shape, action_shape):
        super().__init__()
        self.model = nn.Sequential(*[
            nn.Linear(np.prod(state_shape), 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, np.prod(action_shape))
        ])

    def forward(self, obs, state=None, info={}):
        if not isinstance(obs, torch.Tensor):
            obs = torch.tensor(obs, dtype=torch.float)
        batch = obs.shape[0]
        logits = self.model(obs.view(batch, -1))
        return logits, state


def serial_pipeline(cfg, seed: int = 0):

    env = gym.make(cfg.env.env_id)
    train_envs = gym.make(cfg.env.env_id)
    test_envs = gym.make(cfg.env.env_id)

    state_shape = env.observation_space.shape or env.observation_space.n
    action_shape = env.action_space.shape or env.action_space.n
    net = Net(state_shape, action_shape)
    optim = torch.optim.Adam(net.parameters(),
                             lr=cfg.policy.learn.learning_rate)

    policy = ts.policy.DQNPolicy(net,
                                 optim,
                                 discount_factor=0.9,
                                 estimation_step=3,
                                 target_update_freq=320)

    train_collector = ts.data.Collector(policy,
                                        train_envs,
                                        ts.data.VectorReplayBuffer(20000, 10),
                                        exploration_noise=True)
    test_collector = ts.data.Collector(policy,
                                       test_envs,
                                       exploration_noise=True)

    result = ts.trainer.offpolicy_trainer(
        policy,
        train_collector,
        test_collector,
        max_epoch=10,
        step_per_epoch=10000,
        step_per_collect=10,
        update_per_step=0.1,
        episode_per_test=100,
        batch_size=cfg.policy.learn.batch_size,
        train_fn=lambda epoch, env_step: policy.set_eps(0.1),
        test_fn=lambda epoch, env_step: policy.set_eps(0.05),
        stop_fn=lambda mean_rewards: mean_rewards >= env.spec.reward_threshold)
    print(f'Finished training! Use {result["duration"]}')

    import os
    import time
    import pickle
    import numpy as np
    if not os.path.exists(cfg.exp_name):
        os.makedirs(cfg.exp_name)
    with open(os.path.join(cfg.exp_name, 'result.pkl'), 'wb') as f:
        final_data = {
            'duration': result["duration"],
            'test_step': result["test_step"],
            'train_step': result["train_step"],
            'best_reward': result["best_reward"],
        }
        pickle.dump(final_data, f)


if __name__ == "__main__":
    serial_pipeline(main_config)
