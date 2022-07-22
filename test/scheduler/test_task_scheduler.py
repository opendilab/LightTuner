import os
import time
import string
import random
from unittest import mock
from unittest.mock import patch
import shutil
import pytest

import copy
import pickle

from ditk.scheduler import Scheduler, Task


def clean_up(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)


def mock_run_kubectl_check_status_none(task_name: str) -> str:
    return ""


def mock_run_kubectl_check_status_pending(task_name: str) -> str:
    return "'Pending'"


def mock_run_kubectl_check_status_running(task_name: str) -> str:
    return "'Running'"


def mock_run_kubectl_check_status_succeeded(task_name: str) -> str:
    return "'Succeeded'"


def mock_run_kubectl_check_status_failed(task_name: str) -> str:
    return "'Failed'"


def mock_run_kubectl_check_status_unknown(task_name: str) -> str:
    return "'Unknown'"


def mock_run_kubectl_check_no_file(
        task_name: str, _k8s_remote_project_path: str, _dijob_project_name: str, file_name: str
) -> str:
    return ""


def mock_run_kubectl_check_file(
        task_name: str, _k8s_remote_project_path: str, _dijob_project_name: str, file_name: str
) -> str:
    return file_name


def mock_run_kubectl_copy_no_file(
        task_name: str, _k8s_remote_project_path: str, _dijob_project_name: str, file_name: str, file_saved_path: str
) -> None:
    pass


def mock_run_kubectl_copy_file(
        task_name: str, _k8s_remote_project_path: str, _dijob_project_name: str, file_name: str, file_saved_path: str
) -> None:
    result = {"eval_value": 100 + random.random()}
    with open(file_saved_path, "wb") as f:
        pickle.dump(result, f)


@pytest.mark.unittest
class TestTask:

    def test_config(self):
        rl_task = Task()

        assert rl_task.defined is False
        assert rl_task.running is False
        assert rl_task.waiting is False
        assert rl_task.finish is False
        assert rl_task.success is False
        assert rl_task.normal is True
        assert rl_task.pid is None
        assert rl_task.process is None
        assert rl_task.start_time is None

        example_hyper_parameter = {"DI-toolkit-hpo-id": 0, "p1": 1, "p2": 2}
        rl_task.define(task_id=100, hpo_project_name="cartpole", hyper_parameter_info=example_hyper_parameter)

        assert rl_task.task_name == "cartpole-hpo-id-0-task-100"
        assert rl_task.hyper_parameter_info == example_hyper_parameter
        assert rl_task.defined is True
        assert rl_task.running is False
        assert rl_task.waiting is False
        assert rl_task.finish is False
        assert rl_task.success is False
        assert rl_task.normal is True
        assert rl_task.pid is None
        assert rl_task.process is None
        assert rl_task.start_time is None

    def test_write_config_file(self):

        example_hyper_parameter = {"DI-toolkit-hpo-id": 0, "p1": 1, "p2": 2}
        rl_config_template_file_path = "./unittest_for_scheduler/rl_config_template_file.py"
        rl_config_file_path = "./unittest_for_scheduler/rl_config_file.py"

        if not os.path.exists(os.path.dirname(rl_config_template_file_path)):
            os.makedirs(os.path.dirname(rl_config_template_file_path))

        with open(rl_config_template_file_path, mode="w", encoding="UTF-8") as f:
            f.write('from easydict import EasyDict\n')
            f.write('main_config = EasyDict({})\n')
            f.write('if __name__ == "__main__":\n')
            f.write('    return 0\n')

        origin_lines = None
        with open(rl_config_template_file_path, mode="r", encoding="UTF-8") as f:
            origin_lines = f.read().splitlines()

        extra_lines = []
        extra_lines.append('main_config["DI-toolkit-hpo-id"] = 0')
        extra_lines.append('main_config["p1"] = 1')
        extra_lines.append('main_config["p2"] = 2')
        extra_lines.append('main_config["exp_name"] = "cartpole-hpo-id-0-task-100"')

        rl_task = Task()
        rl_task.define(task_id=100, hpo_project_name="cartpole", hyper_parameter_info=example_hyper_parameter)
        rl_task.write_config_file(
            task_config_template_path=rl_config_template_file_path, rl_config_file_path=rl_config_file_path
        )

        assert os.path.exists(rl_config_file_path)

        with open(rl_config_file_path, mode="r", encoding="UTF-8") as f:
            lines = f.read().splitlines()
            for i, _ in enumerate(lines):
                if i <= 1:
                    assert lines[i] == origin_lines[i]
                elif i >= len(lines) - 2:
                    assert lines[i] == origin_lines[i + 4 - len(lines)]
                else:
                    assert lines[i] == extra_lines[i - 2]

        clean_up("./unittest_for_scheduler/")


@pytest.mark.unittest
class TestTaskScheduler:

    def test_scheduler_init_and_config(self):
        example_hyper_parameter = {"DI-toolkit-hpo-id": 0, "p1": 1, "p2": 2}
        rl_config_template_file_path = "./unittest_for_scheduler_init/rl_config_template_file.py"
        k8s_dijob_yaml_file_path = "./unittest_for_scheduler_init/k8s_dijob_yaml_file.py"
        k8s_remote_project_path = "./mnt/lustre/test/"

        if not os.path.exists(os.path.dirname(rl_config_template_file_path)):
            os.makedirs(os.path.dirname(rl_config_template_file_path))

        with open(rl_config_template_file_path, mode="w", encoding="UTF-8") as f:
            f.write('from easydict import EasyDict\n')
            f.write('main_config = EasyDict({})\n')
            f.write('if __name__ == "__main__":\n')
            f.write('    a=1\n')

        scheduler = Scheduler()

        scheduler.config(
            task_config_template_path=rl_config_template_file_path,
            dijob_project_name="cartpole",
            max_number_of_running_task=20,
            max_number_of_tasks=10000,
            mode="k8s",
            time_out=2000,
            mp_queue_input=None,
            mp_queue_output=None,
            k8s_dijob_yaml_file_path=k8s_dijob_yaml_file_path,
            k8s_remote_project_path=k8s_remote_project_path,
        )

        assert scheduler._max_number_of_running_task == 20
        assert scheduler._max_number_of_tasks == 10000
        assert scheduler._dijob_file_folder == "./cartpole/"
        assert scheduler._mode == "k8s"
        assert scheduler._time_out == 2000
        assert scheduler._mp_queue_input is not None
        assert scheduler._mp_queue_output is not None
        mp_queue_input, mp_queue_output = scheduler.get_mp_queues()
        assert id(mp_queue_input) == id(scheduler._mp_queue_input)
        assert id(mp_queue_output) == id(scheduler._mp_queue_output)
        assert scheduler._k8s_dijob_yaml_file_path == k8s_dijob_yaml_file_path
        assert scheduler._k8s_remote_project_path == k8s_remote_project_path

        clean_up("./unittest_for_scheduler_init/")

    def test_define_rl_task(self):
        example_hyper_parameter = {"DI-toolkit-hpo-id": 0, "p1": 1, "p2": 2}
        rl_config_template_file_path = "./unittest_for_scheduler_define/rl_config_template_file.py"

        if not os.path.exists(os.path.dirname(rl_config_template_file_path)):
            os.makedirs(os.path.dirname(rl_config_template_file_path))

        with open(rl_config_template_file_path, mode="w", encoding="UTF-8") as f:
            f.write('from easydict import EasyDict\n')
            f.write('main_config = EasyDict({})\n')
            f.write('if __name__ == "__main__":\n')
            f.write('    a=1\n')

        scheduler = Scheduler()

        scheduler.config(
            task_config_template_path=rl_config_template_file_path,
            dijob_project_name="unittest-scheduler-define",
            max_number_of_running_task=20,
            max_number_of_tasks=10000,
            mode="local",
            time_out=2000,
            mp_queue_input=None,
            mp_queue_output=None,
            k8s_dijob_yaml_file_path=None,
            k8s_remote_project_path=None,
        )

        new_samples = []
        for i in range(2):
            new_sample = example_hyper_parameter
            new_sample["DI-toolkit-hpo-id"] = i + 1
            new_sample["DI-toolkit-scheduler-hpo-id"] = "".join(random.choice(string.ascii_uppercase) for _ in range(8))
            new_samples.append(new_sample)

        assert len(scheduler.task_list) == 0
        assert len(scheduler.task_defined_id) == 0
        scheduler.define_rl_task(new_samples)
        assert len(scheduler.task_list) == 2
        assert len(scheduler.task_defined_id) == 2
        assert scheduler.task_list[1].defined is True
        assert scheduler.task_list[1].hpo_id == "2"

        assert len(scheduler._task_waiting_queue) == 0
        assert scheduler.task_list[1].waiting is False
        scheduler.add_defined_rl_tasks_into_waiting_list()
        assert len(scheduler.task_defined_id) == 2
        assert len(scheduler._task_waiting_queue) == 2
        assert scheduler.task_list[1].waiting is True

        clean_up("./unittest_for_scheduler_define/")
        clean_up("./unittest-scheduler-define/")

    def test_emit_task_local(self):
        example_hyper_parameter = {"DI-toolkit-hpo-id": 0, "p1": 1, "p2": 2}
        rl_config_template_file_path = "./unittest_for_scheduler_local/rl_config_template_file.py"

        if not os.path.exists(os.path.dirname(rl_config_template_file_path)):
            os.makedirs(os.path.dirname(rl_config_template_file_path))

        with open(rl_config_template_file_path, mode="w", encoding="UTF-8") as f:
            f.write('from easydict import EasyDict\n')
            f.write('import time\n')
            f.write('import pickle\n')
            f.write('main_config = EasyDict({})\n')
            f.write('if __name__ == "__main__":\n')
            f.write('    with open("./" + main_config["exp_name"] + "/result.pkl", "wb") as f:\n')
            f.write('        pickle.dump(main_config,f)\n')
            f.write('    time.sleep(3)\n')

        scheduler = Scheduler()

        scheduler.config(
            task_config_template_path=rl_config_template_file_path,
            dijob_project_name="unittest-cartpole-local",
            max_number_of_running_task=2,
            max_number_of_tasks=2,
            mode="local",
            time_out=2.5,
            mp_queue_input=None,
            mp_queue_output=None,
            k8s_dijob_yaml_file_path=None,
            k8s_remote_project_path=None,
        )

        new_samples = []
        for i in range(2):
            new_sample = example_hyper_parameter
            new_sample["DI-toolkit-hpo-id"] = i + 1
            new_sample["DI-toolkit-scheduler-hpo-id"] = \
                "".join(random.choice(string.ascii_uppercase) for _ in range(8))
            new_samples.append(copy.deepcopy(new_sample))

        scheduler.define_rl_task(new_samples)
        scheduler.add_defined_rl_tasks_into_waiting_list()

        assert len(scheduler.task_waiting_id) == 2
        assert len(scheduler.task_running_id) == 0
        assert len(scheduler._task_waiting_queue) == 2
        assert scheduler.count_running_tasks() == 0
        scheduler.emit_task(0)
        scheduler.emit_task(1)
        assert len(scheduler.task_waiting_id) == 0
        assert len(scheduler.task_running_id) == 2
        assert scheduler.count_running_tasks() == 2

        scheduler.check_task_start(scheduler.task_list[0])
        scheduler.check_task_start(scheduler.task_list[1])

        assert scheduler.check_task_alive(scheduler.task_list[0])
        assert scheduler.check_task_alive(scheduler.task_list[1])
        assert not scheduler.check_task_timeout(scheduler.task_list[0])
        assert not scheduler.check_task_timeout(scheduler.task_list[1])
        scheduler.cancel_task(1)
        assert not scheduler.check_task_alive(scheduler.task_list[1])
        time.sleep(6)
        assert not scheduler.check_task_alive(scheduler.task_list[0])
        assert scheduler.check_task_timeout(scheduler.task_list[0])
        assert scheduler.check_task_timeout(scheduler.task_list[1])

        assert not scheduler.check_finish()
        scheduler.task_list[0].success = True
        scheduler.task_list[1].success = True
        assert scheduler.check_finish()

        data, _ = scheduler.load_task_result(scheduler.task_list[0])
        assert isinstance(data, dict)

        scheduler.check_running_tasks()
        assert len(scheduler.task_running_id) == 0
        assert len(scheduler.task_finished_id) == 2
        assert len(scheduler.task_success_id) == 1

        report_num = scheduler._mp_queue_output.qsize()
        scheduler.report_status()
        assert scheduler._mp_queue_output.qsize() == report_num + 1

        report_num = scheduler._mp_queue_input.qsize()
        scheduler.stop()
        assert scheduler._mp_queue_input.qsize() == report_num + 1

        clean_up("./unittest_for_scheduler_local/")
        clean_up("./unittest-cartpole-local/")

    @patch('ditk.scheduler.task_scheduler._run_kubectl')
    def test_emit_task_k8s(self, mock_run_kubectl):

        mock_run_kubectl.return_value = None

        example_hyper_parameter = {"DI-toolkit-hpo-id": 0, "p1": 1, "p2": 2}
        rl_config_template_file_path = "./unittest_for_scheduler_k8s/rl_config_template_file.py"
        k8s_dijob_yaml_file_path = "./unittest_for_scheduler_k8s/k8s_dijob_yaml_file.yml"
        k8s_remote_project_path = "/mnt/lustre/unittest_for_scheduler_k8s/"

        if not os.path.exists(os.path.dirname(rl_config_template_file_path)):
            os.makedirs(os.path.dirname(rl_config_template_file_path))

        with open(rl_config_template_file_path, mode="w", encoding="UTF-8") as f:
            f.write('from easydict import EasyDict\n')
            f.write('import time\n')
            f.write('import pickle\n')
            f.write('main_config = EasyDict({})\n')
            f.write('if __name__ == "__main__":\n')
            f.write('    with open("./" + main_config["exp_name"] + "/result.pkl", "wb") as f:\n')
            f.write('        pickle.dump(main_config,f)\n')
            f.write('    time.sleep(3)\n')

        with open(k8s_dijob_yaml_file_path, mode="w", encoding="UTF-8") as f:
            f.write('apiVersion: diengine.opendilab.org/v2alpha1\n')
            f.write('kind: DIJob\n')
            f.write('metadata:\n')
            f.write('  name: cartpole-dqn-hpo-k8s\n')
            f.write('  projectPath: /mnt/lustre/unittest_for_scheduler_k8s/\n')
            f.write('spec:\n')
            f.write('  tasks:\n')
            f.write('  - replicas: 1\n')
            f.write('    template:\n')
            f.write('      spec:\n')
            f.write('        containers:\n')
            f.write('        - name: di-container\n')
            f.write('        volumes:\n')
            f.write('        - name: config-py\n')
            f.write('          configMap:\n')
            f.write('            name: config-py-\n')
            f.write('---\n')
            f.write('apiVersion: v1\n')
            f.write('kind: ConfigMap\n')
            f.write('metadata:\n')
            f.write('  name: config-py-\n')
            f.write('data:\n')
            f.write('  config.py: |\n')
            f.write('\n')

        scheduler = Scheduler()

        scheduler.config(
            task_config_template_path=rl_config_template_file_path,
            dijob_project_name="unittest-cartpole-k8s",
            max_number_of_running_task=4,
            max_number_of_tasks=4,
            mode="k8s",
            time_out=2.5,
            mp_queue_input=None,
            mp_queue_output=None,
            k8s_dijob_yaml_file_path=k8s_dijob_yaml_file_path,
            k8s_remote_project_path=k8s_remote_project_path,
        )

        new_samples = []
        for i in range(4):
            new_sample = example_hyper_parameter
            new_sample["DI-toolkit-hpo-id"] = i + 1
            new_sample["DI-toolkit-scheduler-hpo-id"] = \
                "".join(random.choice(string.ascii_uppercase) for _ in range(8))
            new_samples.append(copy.deepcopy(new_sample))

        scheduler.define_rl_task(new_samples)
        scheduler.add_defined_rl_tasks_into_waiting_list()

        scheduler.emit_task(0)
        scheduler.emit_task(1)

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_pending) as mock_func:
            scheduler.check_task_start(scheduler.task_list[0])
            assert scheduler.task_list[0].start_time is None
        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_running) as mock_func:
            scheduler.check_task_start(scheduler.task_list[0])
            assert scheduler.task_list[0].start_time is not None
            scheduler.check_task_start(scheduler.task_list[1])

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_none) as mock_func:
            assert scheduler.check_task_alive(scheduler.task_list[0]) is False
        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_pending) as mock_func:
            assert scheduler.check_task_alive(scheduler.task_list[0]) is True
        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_running) as mock_func:
            assert scheduler.check_task_alive(scheduler.task_list[0]) is True
        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_succeeded) as mock_func:
            assert scheduler.check_task_alive(scheduler.task_list[0]) is False
        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_failed) as mock_func:
            assert scheduler.check_task_alive(scheduler.task_list[0]) is False
        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_unknown) as mock_func:
            assert scheduler.check_task_alive(scheduler.task_list[0]) is False

        scheduler.cancel_task(1)

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_file",
                   wraps=mock_run_kubectl_check_no_file) as mock_func:
            with patch("ditk.scheduler.task_scheduler._run_kubectl_copy_file",
                       wraps=mock_run_kubectl_copy_no_file) as mock_func:
                data, _ = scheduler.load_task_result(scheduler.task_list[0])
                assert data is None

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_file",
                   wraps=mock_run_kubectl_check_file) as mock_func:
            with patch("ditk.scheduler.task_scheduler._run_kubectl_copy_file",
                       wraps=mock_run_kubectl_copy_file) as mock_func:
                data, _ = scheduler.load_task_result(scheduler.task_list[0])
                assert isinstance(data, dict)

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_running) as mock_func:
            with patch("ditk.scheduler.task_scheduler._run_kubectl_check_file",
                       wraps=mock_run_kubectl_check_no_file) as mock_func:
                with patch("ditk.scheduler.task_scheduler._run_kubectl_copy_file",
                           wraps=mock_run_kubectl_copy_no_file) as mock_func:
                    assert len(scheduler.task_running_id) == 2
                    assert len(scheduler.task_finished_id) == 0
                    assert len(scheduler.task_success_id) == 0
                    scheduler.check_running_tasks()
                    assert len(scheduler.task_running_id) == 2
                    assert len(scheduler.task_finished_id) == 0
                    assert len(scheduler.task_success_id) == 0

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_running) as mock_func:
            with patch("ditk.scheduler.task_scheduler._run_kubectl_check_file",
                       wraps=mock_run_kubectl_check_file) as mock_func:
                with patch("ditk.scheduler.task_scheduler._run_kubectl_copy_file",
                           wraps=mock_run_kubectl_copy_file) as mock_func:
                    assert len(scheduler.task_running_id) == 2
                    assert len(scheduler.task_finished_id) == 0
                    assert len(scheduler.task_success_id) == 0
                    scheduler.check_running_tasks()
                    assert len(scheduler.task_running_id) == 0
                    assert len(scheduler.task_finished_id) == 2
                    assert len(scheduler.task_success_id) == 2

        scheduler.emit_task(2)

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_running) as mock_func:
            with patch("ditk.scheduler.task_scheduler._run_kubectl_check_file",
                       wraps=mock_run_kubectl_check_no_file) as mock_func:
                with patch("ditk.scheduler.task_scheduler._run_kubectl_copy_file",
                           wraps=mock_run_kubectl_copy_no_file) as mock_func:

                    assert len(scheduler.task_running_id) == 1
                    assert len(scheduler.task_finished_id) == 2
                    assert len(scheduler.task_success_id) == 2
                    scheduler.check_running_tasks()
                    assert len(scheduler.task_running_id) == 1
                    assert len(scheduler.task_finished_id) == 2
                    assert len(scheduler.task_success_id) == 2

        time.sleep(4)

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_running) as mock_func:
            with patch("ditk.scheduler.task_scheduler._run_kubectl_check_file",
                       wraps=mock_run_kubectl_check_no_file) as mock_func:
                with patch("ditk.scheduler.task_scheduler._run_kubectl_copy_file",
                           wraps=mock_run_kubectl_copy_no_file) as mock_func:
                    assert len(scheduler.task_running_id) == 1
                    assert len(scheduler.task_finished_id) == 2
                    assert len(scheduler.task_success_id) == 2
                    scheduler.check_running_tasks()
                    assert len(scheduler.task_running_id) == 0
                    assert len(scheduler.task_finished_id) == 3
                    assert len(scheduler.task_success_id) == 2
                    assert len(scheduler.task_abnormal_id) == 1

        scheduler.emit_task(3)

        with patch("ditk.scheduler.task_scheduler._run_kubectl_check_status",
                   wraps=mock_run_kubectl_check_status_none) as mock_func:
            with patch("ditk.scheduler.task_scheduler._run_kubectl_check_file",
                       wraps=mock_run_kubectl_check_no_file) as mock_func:
                with patch("ditk.scheduler.task_scheduler._run_kubectl_copy_file",
                           wraps=mock_run_kubectl_copy_no_file) as mock_func:
                    assert len(scheduler.task_running_id) == 1
                    assert len(scheduler.task_finished_id) == 3
                    assert len(scheduler.task_success_id) == 2
                    assert len(scheduler.task_abnormal_id) == 1
                    scheduler.check_running_tasks()
                    assert len(scheduler.task_running_id) == 0
                    assert len(scheduler.task_finished_id) == 4
                    assert len(scheduler.task_success_id) == 2
                    assert len(scheduler.task_abnormal_id) == 2

        clean_up("./unittest_for_scheduler_k8s/")
        clean_up("./unittest-cartpole-k8s/")
