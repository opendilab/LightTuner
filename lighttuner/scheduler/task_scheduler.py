"""task scheduler for DI-engine"""
import copy
import json
import multiprocessing
import os
import pickle
import queue
import random
import string
import subprocess
import sys
import threading
import time
import traceback
from collections import deque
from typing import Callable, List, Tuple

from ditk import logging
from ruamel.yaml import YAML
from tabulate import tabulate

from .cross_platform_mp_queue import MPQueue


def parse_dict(info_dict: dict) -> List:
    """
    parse deep dict into list.
    """
    info_parsed = []
    for key, value in info_dict.items():
        if isinstance(value, dict):
            value_parsed = parse_dict(value)
            for item in value_parsed:
                info_parsed.append([key] + item)
        else:
            info_parsed.append([key, value])
    return info_parsed


def verify_k8s_pod_name(pod_name: str) -> None:
    """
    To abey the naming rule of k8s.
    """
    assert 0 < len(pod_name) < 64, 'Pod name length should be positive and smaller than 64.'
    name = [c for c in pod_name if c.islower() or c.isdigit() or c == "-"]
    assert len(name) == len(pod_name), "Only lowercase aphanumeric character or '-' is allowed in pod name."
    assert pod_name[0].isalnum(), "First character has to be character or digit."


def _run_local(command, log_file: str, end_event, directory: str = "./") -> None:
    """
    for run python in shell
    """
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))
    if not os.path.exists(directory):
        os.makedirs(directory)
    fd = open(log_file, "w", encoding="UTF-8")
    subprocess.run(command, shell=False, stderr=fd, cwd=directory, check=False)
    fd.close()
    end_event.set()


def _run_kubectl(command, log_file: str = None, directory: str = "./") -> None:
    """
    for run kubectl in shell
    """
    if log_file is not None:
        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))
        if not os.path.exists(os.path.dirname(directory)):
            os.makedirs(os.path.dirname(directory))
        fd = open(log_file, "w", encoding="UTF-8")
        subprocess.run(command, shell=False, stdout=fd, stderr=fd, cwd=directory, check=False)
        fd.close()
    else:
        subprocess.run(command, shell=False, cwd=directory, check=False)


def _run_kubectl_check_status(task_name: str) -> str:
    p = subprocess.run(
        ["kubectl", "get", "pod", task_name + "-serial-0", "--no-headers", "-o", "jsonpath='{.status.phase}'"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        cwd="./",
        check=False
    )
    status = p.stdout.decode()
    return status


def _run_kubectl_check_file(
        task_name: str, _k8s_remote_project_path: str, _dijob_project_name: str, file_name: str
) -> str:
    p = subprocess.run(
        [
            "kubectl", "exec", "-i", task_name + "-serial-0", "--", "ls",
            _k8s_remote_project_path + _dijob_project_name + "/" + task_name + "/" + file_name
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        cwd="./",
        check=False
    )
    value = p.stdout.decode()
    return value


def _run_kubectl_copy_file(
        task_name: str, _k8s_remote_project_path: str, _dijob_project_name: str, file_name: str, file_saved_path: str
) -> None:
    with open(os.devnull) as nullstd:
        subprocess.run(
            [
                "kubectl", "cp", task_name + "-serial-0:" + _k8s_remote_project_path + _dijob_project_name + "/" +
                task_name + "/" + file_name, file_saved_path
            ],
            shell=False,
            stdout=nullstd,
            stderr=nullstd,
            cwd="./",
            check=False
        )


class Task:
    """
    The atomic task unit of scheduler, which contains the necessary information for schedule a task.
    """

    def __init__(self):
        self.task_id = None
        self.hpo_id = None
        self.task_name = None
        self.defined = False
        self.running = False
        self.waiting = False
        self.finish = False
        self.success = False
        self.normal = True
        self.hyper_parameter_info = {}
        self.pid = None
        self.process = None
        self.start_time = None
        self.emit_time = None

    def define(self, task_id: int, hpo_project_name: str, hyper_parameter_info: dict) -> None:
        """config a task."""
        self.task_id = task_id
        if "DI-toolkit-hpo-id" in hyper_parameter_info.keys():
            self.hpo_id = str(hyper_parameter_info["DI-toolkit-hpo-id"])
        else:
            self.hpo_id = str(task_id + 1)
        self.task_name = hpo_project_name + "-hpo-id-" + str(self.hpo_id) + "-task-" + str(self.task_id)
        self.hyper_parameter_info = hyper_parameter_info
        self.defined = True

    def write_config_file(self, task_config_template_path: str, rl_config_file_path: str) -> None:
        """write config file as a python file."""

        if not os.path.exists(os.path.dirname(rl_config_file_path)):
            os.makedirs(os.path.dirname(rl_config_file_path))

        config_file_strings = self.generate_config_file(task_config_template_path)
        with open(rl_config_file_path, mode="w", encoding="UTF-8") as f:
            for item in config_file_strings:
                f.write(item + "\n")

    def generate_config_file(self, task_config_template_path: str) -> List[str]:
        """generate config file as string list."""
        config_file_strings = []
        with open(task_config_template_path, mode="r", encoding="UTF-8") as f:
            for line in f.read().splitlines():
                if line == 'if __name__ == "__main__":' or line == "if __name__ == '__main__':":
                    config_file_strings = config_file_strings + self.generate_extra_config()
                config_file_strings.append(line)
        return config_file_strings

    def generate_extra_config(self) -> List[str]:
        """generate extra config as string list."""
        config_file_strings = []

        if "exp_name" not in self.hyper_parameter_info:
            self.hyper_parameter_info["exp_name"] = self.task_name

        hyper_parameter_list = parse_dict(self.hyper_parameter_info)
        for item in hyper_parameter_list:
            hyper_parameter_extra_string = 'main_config'
            for i, _ in enumerate(item):
                if i == len(item) - 1:
                    if isinstance(item[i], str):
                        hyper_parameter_extra_string += ' = ' + '"' + item[i] + '"'
                    else:
                        hyper_parameter_extra_string += ' = ' + str(item[i])
                else:
                    hyper_parameter_extra_string += '["' + str(item[i]) + '"]'
            config_file_strings.append(hyper_parameter_extra_string)

        return config_file_strings

    def get_report(self, return_data=None, result=None):
        """get task basic report."""
        report = {
            "hpo_id": self.hpo_id,
            "task_id": self.task_id,
            "hyper_parameter_info": self.hyper_parameter_info,
        }
        if return_data is not None:
            report.update({"return": return_data})
        if result is not None:
            report.update({"result": result})

        return report


class Scheduler:
    """
    The scheduler module plays the role to schedule tasks and manage the running process.
    """

    def __init__(self):
        self._max_number_of_running_task = 2
        self._max_number_of_tasks = 10
        self.finish = False
        self.task_list = []
        self._task_waiting_queue = deque()
        # ["local", "k8s"]
        self._mode = "local"
        self._time_out = None
        self._task_config_template_path = None
        self._dijob_project_name = None
        self._dijob_file_folder = None

        self._mp_queue_input = None
        self._mp_queue_output = None

        self._k8s_dijob_yaml_file_path = None
        self._k8s_remote_project_path = None

        self.task_defined_id = []
        self.task_running_id = []
        self.task_waiting_id = []
        self.task_finished_id = []
        self.task_success_id = []
        self.task_abnormal_id = []
        self.task_reports = []
        self._last_task_defined_id = []
        self._last_task_running_id = []
        self._last_task_waiting_id = []
        self._last_task_finished_id = []
        self._last_task_success_id = []
        self._last_task_abnormal_id = []

        self._scheduler_monitor_time_interval = 3
        self.monitor_thread = None

    def __enter__(self):
        b = 1
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def config(
            self,
            task_config_template_path: str,
            dijob_project_name: str = None,
            max_number_of_running_task: int = 2,
            max_number_of_tasks: int = 10,
            mode: str = "local",
            time_out: int = None,
            mp_queue_input: MPQueue = None,
            mp_queue_output: MPQueue = None,
            k8s_dijob_yaml_file_path: str = None,
            k8s_remote_project_path: str = None,
    ) -> None:
        """To do scheduler basic configurations."""

        self._max_number_of_running_task = max_number_of_running_task
        self._max_number_of_tasks = max_number_of_tasks
        self._task_config_template_path = task_config_template_path
        if dijob_project_name is None:
            self._dijob_project_name = "dijob-project-" + "".join(random.choice(string.digits) for _ in range(8))
        else:
            self._dijob_project_name = dijob_project_name

        if mode == "k8s":
            verify_k8s_pod_name(self._dijob_project_name)

        self._dijob_file_folder = "./" + dijob_project_name + "/"

        if not os.path.exists(self._dijob_file_folder):
            os.makedirs(self._dijob_file_folder)

        self._mode = mode

        if time_out:
            self._time_out = time_out

        if mp_queue_input:
            self._mp_queue_input = mp_queue_input
        else:
            self._mp_queue_input = MPQueue()
        if mp_queue_output:
            self._mp_queue_output = mp_queue_output
        else:
            self._mp_queue_output = MPQueue()

        if mode == "k8s":
            self._k8s_dijob_yaml_file_path = k8s_dijob_yaml_file_path
            self._k8s_remote_project_path = k8s_remote_project_path

    def get_mp_queues(self) -> Tuple[MPQueue]:
        """return scheduler multiprocessing queues."""
        if self._mp_queue_input is not None and self._mp_queue_output is not None:
            return self._mp_queue_input, self._mp_queue_output
        else:
            return None

    def run(self) -> None:
        """running process of scheduler"""
        while not self.finish:
            if self.count_running_tasks() < self._max_number_of_running_task:
                if self.monitor_resource() and len(self._task_waiting_queue) > 0:
                    task_id = self._task_waiting_queue.popleft()
                    self.emit_task(task_id)

            self.monitor_real_tasks()

            self.report_status()
            time.sleep(self._scheduler_monitor_time_interval)

    def count_running_tasks(self) -> int:
        """counting running tasks number"""
        num = 0
        for rl_task in self.task_list:
            if rl_task.running:
                num += 1
        return num

    def load_task_result(self, rl_task: Task) -> Tuple[dict]:
        """load the result file of a task"""
        data = None
        json_data = None
        if self._mode == "local":

            result_file_path = self._dijob_file_folder + rl_task.task_name + "/result.pkl"
            if os.path.exists(result_file_path):
                with open(result_file_path, "rb") as file:
                    data = pickle.load(file)

            result_json_file_path = self._dijob_file_folder + rl_task.task_name + "/result.txt"
            if os.path.exists(result_json_file_path):
                with open(result_json_file_path, "r", encoding="UTF-8") as file:
                    json_data = json.load(file)

        elif self._mode == "k8s":

            result_file_path = os.path.join(
                self._k8s_remote_project_path, self._dijob_file_folder, rl_task.task_name, 'result.pkl'
            )
            result_json_file_path = os.path.join(
                self._k8s_remote_project_path, self._dijob_file_folder, rl_task.task_name, 'result.txt'
            )

            if os.path.exists(result_file_path):
                with open(result_file_path, "rb") as file:
                    data = pickle.load(file)

                if os.path.exists(result_json_file_path):
                    with open(result_json_file_path, "r", encoding="UTF-8") as file:
                        json_data = json.load(file)
            else:  # remote call k8s

                result_file_path = self._dijob_file_folder + rl_task.task_name + "/result.pkl"
                result_json_file_path = self._dijob_file_folder + rl_task.task_name + "/result.txt"

                if not os.path.exists(os.path.dirname(result_file_path)):
                    os.makedirs(os.path.dirname(result_file_path))

                value = _run_kubectl_check_file(
                    rl_task.task_name, self._k8s_remote_project_path, self._dijob_project_name, "result.pkl"
                )

                if value != "":
                    _run_kubectl_copy_file(
                        rl_task.task_name, self._k8s_remote_project_path, self._dijob_project_name, "result.pkl",
                        result_file_path
                    )

                    if os.path.exists(result_file_path):
                        with open(result_file_path, "rb") as file:
                            data = pickle.load(file)

                json_value = _run_kubectl_check_file(
                    rl_task.task_name, self._k8s_remote_project_path, self._dijob_project_name, "result.txt"
                )

                if json_value != "":
                    with open(result_json_file_path, "w", encoding="UTF-8") as file:
                        file.write(json_value)
                    with open(result_json_file_path, "r", encoding="UTF-8") as file:
                        try:
                            json_data = json.load(file)
                        except Exception as e:
                            logging.warning("Scheduler: invalid json data result file.")
                            json_data = None

        return data, json_data

    def check_task_start(self, rl_task: Task) -> None:
        """check if task has started"""
        if self._mode == "local":
            if rl_task.start_time is None:
                rl_task.start_time = time.time()
        elif self._mode == "k8s":
            if rl_task.start_time is None:
                status = _run_kubectl_check_status(rl_task.task_name)
                if status == "'Pending'":
                    pass
                else:
                    rl_task.start_time = time.time()

    def check_task_alive(self, rl_task) -> bool:
        """check if task is running or ended"""
        if self._mode == "local":
            return not rl_task.end_event.is_set()
        elif self._mode == "k8s":
            status = _run_kubectl_check_status(rl_task.task_name)
            if status == "'Pending'" or status == "'Running'":
                return True
            elif status == "'Succeeded'" or status == "'Failed'" or status == "'Unknown'":
                return False
            else:
                logging.warning("Scheduler: Unknown Error in checking k8s job: " + rl_task.task_name)
                return False

        else:
            return False

    def check_task_timeout(self, rl_task: Task) -> bool:
        """check if task is timeout"""
        if self._time_out is not None and rl_task.start_time is not None:
            if time.time() - rl_task.start_time > self._time_out:
                return True
            else:
                return False
        else:
            return False

    def check_running_tasks(self) -> None:
        """check and manage all tasks that are running"""
        if self._mode == "local":
            for rl_task in self.task_list:
                if rl_task.running:
                    self.check_task_start(rl_task)

                    if self.check_task_alive(rl_task):
                        if self.check_task_timeout(rl_task):
                            self.cancel_task(rl_task.task_id)
                    else:
                        rl_task.process.terminate()
                        rl_task.running = False
                        self.task_running_id.remove(rl_task.task_id)

                        data, json_data = self.load_task_result(rl_task)
                        if data is not None:
                            json_result = {"status": "success"}
                            if json_data is not None:
                                json_result.update(json_data)
                            report = rl_task.get_report(return_data=data, result=json_result)

                            rl_task.finish = True
                            rl_task.success = True
                            rl_task.normal = True
                            self.task_finished_id.append(rl_task.task_id)
                            self.task_success_id.append(rl_task.task_id)
                            self.task_reports.append(report)
                        else:
                            report = rl_task.get_report(result={"status": "fail"})

                            rl_task.finish = True
                            rl_task.success = False
                            rl_task.normal = False
                            self.task_finished_id.append(rl_task.task_id)
                            self.task_abnormal_id.append(rl_task.task_id)
                            self.task_reports.append(report)

        elif self._mode == "k8s":
            for rl_task in self.task_list:
                if rl_task.running:
                    self.check_task_start(rl_task)

                    if self.check_task_alive(rl_task):
                        if self.check_task_timeout(rl_task):
                            report = rl_task.get_report(result={"status": "time out"})

                            rl_task.running = False
                            rl_task.finish = True
                            rl_task.success = False
                            rl_task.normal = False
                            self.task_finished_id.append(rl_task.task_id)
                            self.task_running_id.remove(rl_task.task_id)
                            self.task_abnormal_id.append(rl_task.task_id)
                            self.cancel_task(rl_task.task_id)
                            self.task_reports.append(report)
                    else:
                        # task failed or task emited but not found in few seconds but will start later.
                        rl_task.running = False
                        rl_task.finish = True
                        rl_task.success = False
                        self.task_finished_id.append(rl_task.task_id)
                        self.task_running_id.remove(rl_task.task_id)

                if rl_task.running:
                    data, json_data = self.load_task_result(rl_task)
                    if data is not None:
                        json_result = {"status": "success"}
                        if json_data is not None:
                            json_result.update(json_data)
                        report = rl_task.get_report(return_data=data, result=json_result)

                        rl_task.running = False
                        rl_task.finish = True
                        rl_task.success = True
                        self.task_finished_id.append(rl_task.task_id)
                        self.task_success_id.append(rl_task.task_id)
                        self.task_running_id.remove(rl_task.task_id)
                        self.cancel_task(rl_task.task_id)
                        self.task_reports.append(report)

                elif rl_task.normal and rl_task.task_id not in self.task_success_id \
                        and rl_task.task_id in self.task_finished_id:
                    # check for a second time after sleep
                    time.sleep(5)
                    if self.check_task_alive(rl_task):
                        rl_task.running = True
                        rl_task.finish = False
                        self.task_finished_id.remove(rl_task.task_id)
                        self.task_running_id.append(rl_task.task_id)
                    else:
                        if time.time() - rl_task.emit_time > 180:
                            report = rl_task.get_report(result={"status": "fail"})
                            rl_task.normal = False
                            self.task_abnormal_id.append(rl_task.task_id)
                            self.cancel_task(rl_task.task_id)
                            self.task_reports.append(report)
                        else:
                            logging.warning("Scheduler: Status of k8s job: " + rl_task.task_name \
                                + ", seems to meet some problem.")

    def define_rl_task(self, new_samples: List[dict]) -> None:
        """Add and define new tasks to scheduler"""
        for hyper_parameter_dict in new_samples:
            current_task_list_size = len(self.task_list)
            if current_task_list_size < self._max_number_of_tasks:
                new_task = Task()
                new_task.define(current_task_list_size, self._dijob_project_name, hyper_parameter_dict)
                self.task_list.append(new_task)
                self.task_defined_id.append(new_task.task_id)
        return

    def add_defined_rl_tasks_into_waiting_list(self) -> None:
        """put defined tasks into scheduler waiting queue"""
        for rl_task in self.task_list:
            if rl_task.defined and not rl_task.running and not rl_task.waiting \
                    and not rl_task.finish and not rl_task.success and rl_task.normal:
                self._task_waiting_queue.append(rl_task.task_id)
                rl_task.waiting = True
                self.task_waiting_id.append(rl_task.task_id)

    def check_finish(self) -> bool:
        """check if scheduler is finished"""
        is_finish = False
        if len(self.task_list) >= self._max_number_of_tasks:
            is_finish = True
            for rl_task in self.task_list:
                if not rl_task.success:
                    is_finish = False
        return is_finish

    def monitor_resource(self) -> bool:
        # TODO
        return True

    def monitor_real_tasks(self) -> None:
        """Scheduler monitor routine for task management"""
        self.check_running_tasks()
        if len(self.task_list) < self._max_number_of_tasks:
            new_samples = None
            try:
                new_info = self._mp_queue_input.get(block=False)
                if "stop_scheduler" in new_info:
                    self.finish = True
                    logging.info("Stopping scheduler.")
                else:
                    new_samples = new_info
            except queue.Empty:
                # do nothing if no new data in queue.
                pass

            if new_samples:
                self.define_rl_task(new_samples)
                self.add_defined_rl_tasks_into_waiting_list()
        if not self.finish:
            self.finish = self.check_finish()

    def emit_task(self, task_id: int):
        """make a task to get running"""
        self.task_list[task_id].waiting = False
        self.task_list[task_id].running = True

        if self._mode == "local":
            local_file_name = "hpo-id-" + self.task_list[task_id].hpo_id + "-task-" + str(task_id) + ".py"
            local_main_file_path = self._dijob_file_folder + local_file_name
            self.task_list[task_id].write_config_file(self._task_config_template_path, local_main_file_path)

            main_file = "./" + local_file_name
            log_file = self._dijob_file_folder + self.task_list[task_id].task_name + "-log" + "/log.txt"
            running_directory = self._dijob_file_folder
            command = [sys.executable, main_file]
            end_event = multiprocessing.Event()

            self.task_list[task_id].process = multiprocessing.Process(
                target=_run_local, args=(
                    command,
                    log_file,
                    end_event,
                    running_directory,
                )
            )
            self.task_list[task_id].end_event = end_event
            self.task_list[task_id].process.start()
            self.task_list[task_id].pid = self.task_list[task_id].process.pid
            logging.info(
                "Scheduler: hpo-id-" + self.task_list[task_id].hpo_id + "-task-" + str(task_id) + " emited with pid [" +
                str(self.task_list[task_id].pid) + "]"
            )

        elif self._mode == "k8s":
            with open(self._k8s_dijob_yaml_file_path, mode="r", encoding="UTF-8") as f:

                ryaml = YAML()
                ryaml_content = list(ryaml.load_all(f))

            for content in ryaml_content:
                if content["kind"] == "DIJob":
                    content["metadata"]["name"] = self.task_list[task_id].task_name
                    volumes = content["spec"]["tasks"][0]["template"]["spec"]["volumes"]
                    for volume in volumes:
                        if volume["name"] == "config-py":
                            volume["configMap"]["name"] = "config-py-" + self.task_list[task_id].task_name
                            break
                elif content["kind"] == "ConfigMap":
                    content["metadata"]["name"] = "config-py-" + self.task_list[task_id].task_name

            config_python_code = self.task_list[task_id].generate_config_file(self._task_config_template_path)

            dijob_file = self._dijob_file_folder + "hpo-id-" + self.task_list[
                task_id].hpo_id + "-task-" + str(task_id) + ".yml"

            with open(dijob_file, mode="w", encoding="UTF-8") as f:
                for i in range(len(ryaml_content)):
                    ryaml = YAML()
                    ryaml.dump(ryaml_content[i], f)
                    if ryaml_content[i]["kind"] == "ConfigMap":
                        for code in config_python_code:
                            f.write("    " + code + "\n")

                    if i < len(ryaml_content) - 1:
                        f.write("---\n")

            _run_kubectl(["kubectl", "create", "-f", dijob_file, "--validate=false"])

        self.task_list[task_id].emit_time = time.time()
        self.task_running_id.append(task_id)
        self.task_waiting_id.remove(task_id)

    def cancel_task(self, task_id: int) -> None:
        """cancel a task in advance"""
        if self._mode == "local":
            self.task_list[task_id].end_event.set()
            self.task_list[task_id].process.terminate()
        elif self._mode == "k8s":
            dijob_file = self._dijob_file_folder + "hpo-id-" + self.task_list[
                task_id].hpo_id + "-task-" + str(task_id) + ".yml"
            _run_kubectl(["kubectl", "delete", "-f", dijob_file])
            time.sleep(0.5)

    def report_status(self):
        """generate scheduler report"""
        if self._last_task_defined_id != self.task_defined_id or \
                self._last_task_running_id != self.task_running_id or \
                self._last_task_waiting_id != self.task_waiting_id or \
                self._last_task_finished_id != self.task_finished_id or \
                self._last_task_success_id != self.task_success_id or \
                self._last_task_abnormal_id != self.task_abnormal_id:
            table_header = ['status', 'instances']
            table_data = [
                ("task_defined", ",".join(self.task_list[task_id].hpo_id for task_id in self.task_defined_id)),
                ("task_running", ",".join(self.task_list[task_id].hpo_id for task_id in self.task_running_id)),
                ("task_waiting", ",".join(self.task_list[task_id].hpo_id for task_id in self.task_waiting_id)),
                ("task_finished", ",".join(self.task_list[task_id].hpo_id for task_id in self.task_finished_id)),
                ("task_success", ",".join(self.task_list[task_id].hpo_id for task_id in self.task_success_id)),
                ("task_abnormal", ",".join(self.task_list[task_id].hpo_id for task_id in self.task_abnormal_id)),
            ]
            logging.info("Scheduler: report at time: " + time.strftime("%H:%M:%S", time.localtime()))

            logging.info(tabulate(tabular_data=table_data, headers=table_header, tablefmt='grid'))

            self._last_task_defined_id = copy.deepcopy(self.task_defined_id)
            self._last_task_running_id = copy.deepcopy(self.task_running_id)
            self._last_task_waiting_id = copy.deepcopy(self.task_waiting_id)
            self._last_task_finished_id = copy.deepcopy(self.task_finished_id)
            self._last_task_success_id = copy.deepcopy(self.task_success_id)
            self._last_task_abnormal_id = copy.deepcopy(self.task_abnormal_id)

        if self._mp_queue_output:
            self._mp_queue_output.put(self.task_reports)

    def get_hpo_callable(self) -> Callable:
        """scheduler handler for lighttuner-hpo"""

        def inner(v, tid):
            new_sample_info = v
            logging.info("Scheduler: Add new sample [" + str(tid) + "]: " + str(new_sample_info))

            new_sample_info["DI-toolkit-hpo-id"] = tid
            new_sample_info["DI-toolkit-scheduler-hpo-id"] = "".join(
                random.choice(string.ascii_uppercase) for _ in range(8)
            )

            self._mp_queue_input.put([new_sample_info])
            get_rl_result = False
            rl_result = None
            rl_return = None
            while not get_rl_result:
                time.sleep(0.5)
                report_info = self._mp_queue_output.get()
                if report_info:
                    for data in report_info:
                        result_found = True
                        for key, value in new_sample_info.items():
                            if data["hyper_parameter_info"][key] != value:
                                result_found = False
                                break
                        if result_found:
                            get_rl_result = True

                            rl_result = data["result"]
                            rl_return = data["return"]
                            if rl_result["status"] == "success":
                                logging.info(
                                    "Scheduler: hpo-id-" + str(data["hpo_id"]) + "-task-" + str(data["task_id"]) +
                                    " is successful, of which the return is:"
                                )
                                logging.info(rl_return)
                            else:
                                raise ValueError(
                                    "Scheduler: hpo-id-" + str(data["hpo_id"]) + "-task-" + str(data["task_id"]) +
                                    " is not successful, current status is: " + rl_result["status"]
                                )

                        if get_rl_result:
                            break

            return rl_return

        return inner

    def stop(self):
        """stop inner scheduler"""
        end_signal = {"stop_scheduler": True}
        self._mp_queue_input.put(end_signal)


def scheduler_main(
    task_config_template_path,
    dijob_project_name=None,
    max_number_of_running_task=2,
    max_number_of_tasks=20,
    mode="local",
    time_out=None,
    mp_queue_input=None,
    mp_queue_output=None,
    k8s_dijob_yaml_file_path=None,
    k8s_remote_project_path=None,
    mp_queue_error=None,
):
    """inner scheduler main function"""
    if mp_queue_error is None:
        logging.error("Scheduler: An error multiprocessing queue is \
        needed for monitor scheduler.")
        return

    try:
        logging.try_init_root(logging.INFO)
        scheduler = Scheduler()
        scheduler.config(
            max_number_of_running_task=max_number_of_running_task,
            max_number_of_tasks=max_number_of_tasks,
            task_config_template_path=task_config_template_path,
            dijob_project_name=dijob_project_name,
            k8s_dijob_yaml_file_path=k8s_dijob_yaml_file_path,
            k8s_remote_project_path=k8s_remote_project_path,
            mode=mode,
            time_out=time_out,
            mp_queue_input=mp_queue_input,
            mp_queue_output=mp_queue_output
        )

        scheduler.run()

        logging.info("Scheduler: exit.")
        mp_queue_error.put((
            "Exit",
            " ",
        ))
        return

    except Exception as e:
        tb = traceback.format_exc()
        mp_queue_error.put((
            e,
            tb,
        ))


def monitor_scheduler_thead_main(mp_queue_error):
    """Scheduler Monitor Thread function"""
    e, msg = mp_queue_error.get()
    if e == "Exit":
        logging.info("Scheduler: Monitor exit.")
        return
    else:
        logging.error(msg)
        raise e


def run_scheduler(
        task_config_template_path,
        dijob_project_name=None,
        max_number_of_running_task=10,
        max_number_of_tasks=100000,
        mode="local",
        time_out=None,
        k8s_dijob_yaml_file_path=None,
        k8s_remote_project_path=None,
) -> Scheduler:
    """running scheduler in a subprocess."""
    if mode == "local":
        multiprocessing.set_start_method("spawn")

    scheduler = Scheduler()
    scheduler.config(
        task_config_template_path=task_config_template_path,
        dijob_project_name=dijob_project_name,
        max_number_of_running_task=max_number_of_running_task,
        max_number_of_tasks=max_number_of_tasks,
        mode=mode,
        time_out=time_out,
        k8s_dijob_yaml_file_path=k8s_dijob_yaml_file_path,
        k8s_remote_project_path=k8s_remote_project_path
    )

    mp_queue_input, mp_queue_output = scheduler.get_mp_queues()
    mp_queue_error = MPQueue()

    p = multiprocessing.Process(
        target=scheduler_main,
        args=(
            task_config_template_path,
            dijob_project_name,
            max_number_of_running_task,
            max_number_of_tasks,
            mode,
            time_out,
            mp_queue_input,
            mp_queue_output,
            k8s_dijob_yaml_file_path,
            k8s_remote_project_path,
            mp_queue_error,
        )
    )
    p.start()

    scheduler.monitor_thread = threading.Thread(target=monitor_scheduler_thead_main, args=(mp_queue_error, ))
    scheduler.monitor_thread.start()

    return scheduler


def run_scheduler_local(
        task_config_template_path,
        dijob_project_name=None,
        max_number_of_running_task=2,
        max_number_of_tasks=100000,
        time_out=None,
) -> Scheduler:
    """running scheduler in local mode in a subprocess."""
    return run_scheduler(
        task_config_template_path=task_config_template_path,
        dijob_project_name=dijob_project_name,
        max_number_of_running_task=max_number_of_running_task,
        max_number_of_tasks=max_number_of_tasks,
        mode="local",
        time_out=time_out,
    )


def run_scheduler_k8s(
        task_config_template_path,
        k8s_dijob_yaml_file_path,
        time_out=None,
) -> Scheduler:
    """running scheduler in k8s mode in a subprocess."""
    k8s_remote_project_path = None
    dijob_project_name = None
    max_number_of_running_task = 10000
    max_number_of_tasks = 100000

    with open(k8s_dijob_yaml_file_path, mode="r", encoding="UTF-8") as f:

        ryaml = YAML()
        ryaml_content = list(ryaml.load_all(f))

    for content in ryaml_content:
        if content["kind"] == "DIJob":
            if "projectPath" not in content["metadata"]:
                logging.error(
                    "Scheduler: k8s remote project path is not defined in yaml file, \
                        of which should be assigned in 'metadata.projectPath'."
                )
                return
            dijob_project_name = content["metadata"]["name"]
            k8s_remote_project_path = content["metadata"]["projectPath"]

    if dijob_project_name is None:
        logging.error("Scheduler: no k8s project name is assigned.")
        return
    if k8s_remote_project_path is None:
        logging.error("Scheduler: no k8s remote project path is assigned.")
        return

    return run_scheduler(
        task_config_template_path=task_config_template_path,
        dijob_project_name=dijob_project_name,
        max_number_of_running_task=max_number_of_running_task,
        max_number_of_tasks=max_number_of_tasks,
        mode="k8s",
        time_out=time_out,
        k8s_dijob_yaml_file_path=k8s_dijob_yaml_file_path,
        k8s_remote_project_path=k8s_remote_project_path
    )
