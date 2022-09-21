import os
from sklearn.model_selection import train_test_split
from d3rlpy.algos import DQN
from d3rlpy.datasets import get_cartpole
from d3rlpy.metrics.scorer import td_error_scorer
from d3rlpy.metrics.scorer import average_value_estimation_scorer
from d3rlpy.metrics.scorer import evaluate_on_environment
from easydict import EasyDict

main_config = dict(exp_name='d3rlpy_cartpole_dqn', n_epochs=10)
main_config = EasyDict(main_config)


def main(cfg):
    dataset, env = get_cartpole()
    train_episodes, test_episodes = train_test_split(dataset, test_size=0.2)

    dqn = DQN(use_gpu=False)
    dqn.build_with_dataset(dataset)
    td_error = td_error_scorer(dqn, test_episodes)
    evaluate_scorer = evaluate_on_environment(env)

    dqn.fit(
        train_episodes,
        eval_episodes=test_episodes,
        n_epochs=cfg.n_epochs,
        scorers={
            'td_error': td_error_scorer,
            'value_scale': average_value_estimation_scorer,
            'environment': evaluate_scorer
        }
    )

    rewards = evaluate_scorer(dqn)

    import pickle
    if not os.path.exists(cfg.exp_name):
        os.makedirs(cfg.exp_name)
    dqn.save_model(os.path.join(cfg.exp_name, 'dqn.pt'))
    with open(os.path.join(cfg.exp_name, 'result.pkl'), 'wb') as f:
        final_data = {
            'rewards': rewards,
        }
        pickle.dump(final_data, f)


if __name__ == "__main__":
    main(main_config)
