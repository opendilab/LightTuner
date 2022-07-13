"""task scheduler for DI-engine"""
import os
import string
import sys
import copy
from typing import Callable
import subprocess
import threading
from collections import deque
import random
import time
import multiprocessing
import queue
import traceback
import json
import pickle
import psutil
from ditk import logging
from tabulate import tabulate
from ruamel.yaml import YAML


def parse_dict(info_dict):
    """
    parse deep dict into list.
    """
    info_parsed = []
    for key, value in info_dict.items():
        if type(value) is dict:
            value_parsed = parse_dict(value)
            for item in value_parsed:
                info_parsed.append([key] + item)
        else:
            info_parsed.append([key, value])
    return info_parsed


def verify_k8s_pod_name(pod_name):
    """
    To abey the naming rule of k8s.
    """
    assert 0 < len(
        pod_name
    ) < 64, 'Pod name length should be positive and smaller than 64.'
    name = [c for c in pod_name if c.islower() or c.isdigit() or c == "-"]
    assert len(name) == len(
        pod_name
    ), "Only lowercase aphanumeric character or '-' is allowed in pod name."
    assert pod_name[0].isalnum(
    ), "First character has to be character or digit."


def _run_local(command, log_file, directory="./"):
    """
    for run python in shell
    """
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))
    if not os.path.exists(os.path.dirname(directory)):
        os.makedirs(os.path.dirname(directory))
    fd = open(log_file, "w")
    subprocess.run(command, shell=False, stderr=fd, cwd=directory, check=False)
    fd.close()


def _run_kubectl(command, log_file=None, directory="./"):
    """
    for run kubectl in shell
    """
    if log_file is not None:
        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))
        if not os.path.exists(os.path.dirname(directory)):
            os.makedirs(os.path.dirname(directory))
        fd = open(log_file, "w")
        subprocess.run(command,
                       shell=False,
                       stdout=fd,
                       stderr=fd,
                       cwd=directory,
                       check=False)
        fd.close()
    else:
        subprocess.run(command, shell=False, cwd=directory, check=False)


class task:
    def __init__(self):
        self.task_id = None
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

    def config(self, task_id, hpo_project_name, hyper_parameter_info: dict):
        """config a task."""
        self.task_id = task_id
        self.task_name = hpo_project_name + "-" + str(self.task_id)
        self.hyper_parameter_info = hyper_parameter_info
        self.defined = True

    def write_config_file_to_local(self, task_config_template_path,
                                   rl_config_file_path):
        """write config file as a python file."""
        config_file_strings = self.generate_config_file(
            task_config_template_path)
        with open(rl_config_file_path, mode="w", encoding="UTF-8") as f:
            for item in config_file_strings:
                f.write(item + "\n")

    def write_config_file_to_k8s_configmap(self, task_config_template_path,
                                           k8s_yaml_file_path):
        """write config file into k8s yaml file."""
        config_file_strings = self.generate_config_file(
            task_config_template_path)
        with open(k8s_yaml_file_path, mode="w", encoding="UTF-8") as f:
            for item in config_file_strings:
                f.write(item + "\n")

    def generate_config_file(self, task_config_template_path):
        """generate config file as string list."""
        config_file_strings = []
        with open(task_config_template_path, mode="r", encoding="UTF-8") as f:
            for line in f.read().splitlines():
                if line == 'if __name__ == "__main__":':
                    config_file_strings = config_file_strings + self.generate_extra_config(
                    )
                config_file_strings.append(line)
        return config_file_strings

    def generate_extra_config(self):
        """generate extra config as string list."""
        config_file_strings = []

        if "exp_name" not in self.hyper_parameter_info:
            self.hyper_parameter_info["exp_name"] = self.task_name

        hyper_parameter_list = parse_dict(self.hyper_parameter_info)
        for item in hyper_parameter_list:
            hyper_parameter_extra_string = 'main_config'
            for i in range(len(item)):
                if i == len(item) - 1:
                    if type(item[i]) is str:
                        hyper_parameter_extra_string += ' = ' + '"' + item[
                            i] + '"'
                    else:
                        hyper_parameter_extra_string += ' = ' + str(item[i])
                else:
                    hyper_parameter_extra_string += '["' + str(item[i]) + '"]'
            config_file_strings.append(hyper_parameter_extra_string)

        return config_file_strings

    def get_report(self, return_data=None, result=None):
        report = {
            "id": self.task_id,
            "hyper_parameter_info": self.hyper_parameter_info,
        }
        if return_data is not None:
            report.update({"return": return_data})
        if result is not None:
            report.update({"result": result})

        return report


class Scheduler:
    def __init__(self):
        self._max_number_of_running_task = 2
        self._max_number_of_tasks = 20
        self.finish = False
        self.task_list = []
        self._task_waiting_queue = deque()
        self._mode = "local"  #["local", "k8s"]
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

        self.monitor_thread = None

    def config(
        self,
        task_config_template_path,
        dijob_project_name=None,
        max_number_of_running_task=2,
        max_number_of_tasks=10,
        mode="local",
        time_out=None,
        mp_queue_input=None,
        mp_queue_output=None,
        k8s_dijob_yaml_file_path=None,
        k8s_remote_project_path=None,
    ):
        self._max_number_of_running_task = max_number_of_running_task
        self._max_number_of_tasks = max_number_of_tasks
        self._task_config_template_path = task_config_template_path
        if dijob_project_name is None:
            self._dijob_project_name = "dijob-project-" + "".join(
                random.choice(string.digits) for _ in range(8))
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
            self._mp_queue_input = multiprocessing.Queue()
        if mp_queue_output:
            self._mp_queue_output = mp_queue_output
        else:
            self._mp_queue_output = multiprocessing.Queue()

        if mode == "k8s":
            self._k8s_dijob_yaml_file_path = k8s_dijob_yaml_file_path
            self._k8s_remote_project_path = k8s_remote_project_path

    def get_mp_queues(self):
        """return scheduler multiprocessing queues."""
        if self._mp_queue_input is not None and self._mp_queue_output is not None:
            return self._mp_queue_input, self._mp_queue_output
        else:
            return None

    def run(self):
        """running process of scheduler"""
        while not self.finish:
            if self.count_running_tasks() < self._max_number_of_running_task:
                if self.monitor_resource() and len(
                        self._task_waiting_queue) > 0:
                    task_id = self._task_waiting_queue.popleft()
                    self.task_list[task_id].waiting = False
                    self.task_list[task_id].running = True
                    self.emit_task(task_id)
                    self.task_running_id.append(task_id)
                    self.task_waiting_id.remove(task_id)

            self.monitor_real_tasks()

            self.report_status()
            time.sleep(3)

    def count_running_tasks(self) -> int:
        num = 0
        for rl_task in self.task_list:
            if rl_task.running:
                num += 1
        return num

    def load_task_result(self, rl_task):
        data = None
        json_data = None
        if self._mode == "local":

            result_file_path = "./" + rl_task.task_name + "/result.pkl"
            if os.path.exists(result_file_path):
                with open(result_file_path, "rb") as file:
                    data = pickle.load(file)

            result_json_file_path = "./" + rl_task.task_name + "/results.txt"
            if os.path.exists(result_json_file_path):
                with open(result_json_file_path, "r") as file:
                    json_data = json.load(file)

        elif self._mode == "k8s":

            result_file_path = "./" + rl_task.task_name + "/result.pkl"
            result_json_file_path = "./" + rl_task.task_name + "/results.txt"

            if not os.path.exists(os.path.dirname(result_file_path)):
                os.makedirs(os.path.dirname(result_file_path))

            p = subprocess.run([
                "kubectl", "exec", "-i", rl_task.task_name + "-serial-0", "--",
                "ls", self._k8s_remote_project_path + rl_task.task_name +
                "/result.pkl"
            ],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=False,
                               cwd="./",
                               check=False)
            value = p.stdout.decode()
            if value != "":
                with open(os.devnull) as nullstd:
                    subprocess.run([
                        "kubectl", "cp", rl_task.task_name + "-serial-0:" +
                        self._k8s_remote_project_path + rl_task.task_name +
                        "/result.pkl", result_file_path
                    ],
                                   shell=False,
                                   stdout=nullstd,
                                   stderr=nullstd,
                                   cwd="./",
                                   check=False)

                if os.path.exists(result_file_path):
                    with open(result_file_path, "rb") as file:
                        data = pickle.load(file)

            p = subprocess.run([
                "kubectl", "exec", "-i", rl_task.task_name + "-serial-0", "--",
                "cat", self._k8s_remote_project_path + rl_task.task_name +
                "/results.txt"
            ],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=False,
                               cwd="./",
                               check=False)
            json_value = p.stdout.decode()
            if json_value != "":
                with open(result_json_file_path, "w") as file:
                    file.write(json_value)
                with open(result_json_file_path, "r") as file:
                    json_data = json.load(file)

        return data, json_data

    def check_task_start(self, rl_task):

        if self._mode == "local":
            if rl_task.start_time is None:
                rl_task.start_time = time.time()
        elif self._mode == "k8s":
            if rl_task.start_time is None:
                p = subprocess.run([
                    "kubectl", "get", "pod", rl_task.task_name + "-serial-0",
                    "--no-headers", "-o", "jsonpath='{.status.phase}'"
                ],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=False,
                                   cwd="./",
                                   check=False)
                status = p.stdout.decode()
                if status == "'Pending'":
                    pass
                else:
                    rl_task.start_time = time.time()

    def check_task_alive(self, rl_task) -> bool:
        if self._mode == "local":
            return psutil.pid_exists(rl_task.pid)
        elif self._mode == "k8s":
            p = subprocess.run([
                "kubectl", "get", "pod", rl_task.task_name + "-serial-0",
                "--no-headers", "-o", "jsonpath='{.status.phase}'"
            ],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=False,
                               cwd="./",
                               check=False)
            status = p.stdout.decode()
            if status == "'Pending'" or status == "'Running'":
                return True
            elif status == "'Succeeded'" or status == "'Failed'" or status == "'Unknown'":
                return False
            else:
                logging.info("Scheduler: Unknown Error in checking k8s pod: " +
                             rl_task.task_name)
                return False

        else:
            return False

    def check_task_timeout(self, rl_task) -> bool:
        if self._time_out is not None and rl_task.start_time is not None:
            if time.time() - rl_task.start_time > self._time_out:
                return True
            else:
                return False
        else:
            return False

    def check_running_tasks(self):
        if self._mode == "local":
            for rl_task in self.task_list:
                if rl_task.running:
                    self.check_task_start(rl_task)

                    if self.check_task_alive(rl_task):
                        if self.check_task_timeout(rl_task):
                            self.cancel_task(rl_task.task_id)
                    else:
                        rl_task.running = False
                        self.task_running_id.remove(rl_task.task_id)

                        data, json_data = self.load_task_result(rl_task)
                        if data is not None:
                            json_result = {"status": "success"}
                            if json_data is not None:
                                json_result.update(json_data)
                            report = rl_task.get_report(return_data=data,
                                                        result=json_result)

                            rl_task.finish = True
                            rl_task.success = True
                            rl_task.normal = True
                            self.task_finished_id.append(rl_task.task_id)
                            self.task_success_id.append(rl_task.task_id)
                            self.task_reports.append(report)
                        else:
                            report = rl_task.get_report(
                                result={"status": "fail"})

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
                            report = rl_task.get_report(
                                result={"status": "time out"})

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
                        #task failed or task emited but not found in few seconds but will start later.
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
                        report = rl_task.get_report(return_data=data,
                                                    result=json_result)

                        rl_task.running = False
                        rl_task.finish = True
                        rl_task.success = True
                        self.task_finished_id.append(rl_task.task_id)
                        self.task_success_id.append(rl_task.task_id)
                        self.task_running_id.remove(rl_task.task_id)
                        self.cancel_task(rl_task.task_id)
                        self.task_reports.append(report)

                elif rl_task.normal and rl_task.task_id not in self.task_success_id and rl_task.task_id in self.task_finished_id:
                    #check for a second time after sleep
                    time.sleep(5)
                    if self.check_task_alive(rl_task):
                        rl_task.running = True
                        rl_task.finish = False
                        self.task_finished_id.remove(rl_task.task_id)
                        self.task_running_id.append(rl_task.task_id)
                    else:
                        report = rl_task.get_report(result={"status": "fail"})
                        rl_task.normal = False
                        self.task_abnormal_id.append(rl_task.task_id)
                        self.cancel_task(rl_task.task_id)
                        self.task_reports.append(report)

    def rl_task_config(self, new_samples):
        for hyper_parameter_dict in new_samples:
            current_task_list_size = len(self.task_list)
            if current_task_list_size < self._max_number_of_tasks:
                new_task = task()
                new_task.config(current_task_list_size,
                                self._dijob_project_name, hyper_parameter_dict)
                self.task_list.append(new_task)
                self.task_defined_id.append(new_task.task_id)
        return

    def add_defined_rl_tasks(self):
        for rl_task in self.task_list:
            if rl_task.defined and not rl_task.running and not rl_task.waiting and not rl_task.finish and not rl_task.success and rl_task.normal:
                self._task_waiting_queue.append(rl_task.task_id)
                rl_task.waiting = True
                self.task_waiting_id.append(rl_task.task_id)

    def check_finish(self) -> bool:
        is_finish = False
        if len(self.task_list) >= self._max_number_of_tasks:
            is_finish = True
            for rl_task in self.task_list:
                if not rl_task.success:
                    is_finish = False
        return is_finish

    def monitor_resource(self) -> bool:
        #TODO
        return True

    def monitor_real_tasks(self) -> None:
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
                #do nothing if no new data in queue.
                pass

            if new_samples:
                self.rl_task_config(new_samples)
                self.add_defined_rl_tasks()
        if not self.finish:
            self.finish = self.check_finish()

    def emit_task(self, task_id):
        if self._mode == "local":
            main_file = self._dijob_file_folder + str(task_id) + ".py"
            log_file = self.task_list[task_id].task_name + "/log.txt"
            self.task_list[task_id].write_config_file_to_local(
                self._task_config_template_path, main_file)

            command = [sys.executable, main_file]

            self.task_list[task_id].process = multiprocessing.Process(
                target=_run_local, args=(
                    command,
                    log_file,
                ))
            self.task_list[task_id].process.start()
            self.task_list[task_id].pid = self.task_list[task_id].process.pid
            logging.info("Scheduler: task " + str(task_id) +
                         " emited with pid [" +
                         str(self.task_list[task_id].pid) + "]")

        elif self._mode == "k8s":
            with open(self._k8s_dijob_yaml_file_path,
                      mode="r",
                      encoding="UTF-8") as f:

                ryaml = YAML()
                ryaml_content = list(ryaml.load_all(f))

            for content in ryaml_content:
                if content["kind"] == "DIJob":
                    content["metadata"]["name"] = self.task_list[
                        task_id].task_name
                    volumes = content["spec"]["tasks"][0]["template"]["spec"][
                        "volumes"]
                    for volume in volumes:
                        if volume["name"] == "config-py":
                            volume["configMap"][
                                "name"] = "config-py-" + self.task_list[
                                    task_id].task_name
                            break
                elif content["kind"] == "ConfigMap":
                    content["metadata"][
                        "name"] = "config-py-" + self.task_list[
                            task_id].task_name

            config_python_code = self.task_list[task_id].generate_config_file(
                self._task_config_template_path)

            dijob_file = self._dijob_file_folder + str(task_id) + ".yml"

            with open(dijob_file, mode="w", encoding="UTF-8") as f:
                for i in range(len(ryaml_content)):
                    ryaml = YAML()
                    ryaml.dump(ryaml_content[i], f)
                    if ryaml_content[i]["kind"] == "ConfigMap":
                        for code in config_python_code:
                            f.write("    " + code + "\n")

                    if i < len(ryaml_content) - 1:
                        f.write("---\n")

            _run_kubectl(
                ["kubectl", "create", "-f", dijob_file, "--validate=false"])

    def cancel_task(self, task_id):
        if self._mode == "local":
            self.task_list[task_id].process.terminate()
        elif self._mode == "k8s":
            dijob_file = self._dijob_file_folder + str(task_id) + ".yml"
            _run_kubectl(["kubectl", "delete", "-f", dijob_file])
            time.sleep(1)

    def report_status(self):

        if \
            self._last_task_defined_id!=self.task_defined_id or \
            self._last_task_running_id!=self.task_running_id or \
            self._last_task_waiting_id!=self.task_waiting_id or \
            self._last_task_finished_id!=self.task_finished_id or \
            self._last_task_success_id!=self.task_success_id or \
            self._last_task_abnormal_id!=self.task_abnormal_id:

            table_header = ['status', 'instances']
            table_data = [
                ("task_defined", str(self.task_defined_id)),
                ("task_running", str(self.task_running_id)),
                ("task_waiting", str(self.task_waiting_id)),
                ("task_finished", str(self.task_finished_id)),
                ("task_success", str(self.task_success_id)),
                ("task_abnormal", str(self.task_abnormal_id)),
            ]
            logging.info("Scheduler: report at time: " +
                         time.strftime("%H:%M:%S", time.localtime()))

            logging.info(
                tabulate(tabular_data=table_data,
                         headers=table_header,
                         tablefmt='grid'))

            self._last_task_defined_id = copy.deepcopy(self.task_defined_id)
            self._last_task_running_id = copy.deepcopy(self.task_running_id)
            self._last_task_waiting_id = copy.deepcopy(self.task_waiting_id)
            self._last_task_finished_id = copy.deepcopy(self.task_finished_id)
            self._last_task_success_id = copy.deepcopy(self.task_success_id)
            self._last_task_abnormal_id = copy.deepcopy(self.task_abnormal_id)

        if self._mp_queue_output:
            self._mp_queue_output.put(self.task_reports)

    def get_hpo_callable(self) -> Callable:
        def inner(v):
            new_sample_info = v
            logging.info("Scheduler: Add new sample: " + str(new_sample_info))
            new_sample_info["DI-toolkit-scheduler-hpo-id"] = "".join(
                random.choice(string.ascii_uppercase) for _ in range(8))

            self._mp_queue_input.put([new_sample_info])
            get_rl_result = False
            rl_result = None
            rl_return = None
            while not get_rl_result:
                time.sleep(1)
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
                                    "Scheduler: id[" + str(data["id"]) +
                                    "] is successful, of which the return is:")
                                logging.info(rl_return)
                            else:
                                raise ValueError(
                                    "Scheduler: id[" + str(data["id"]) +
                                    "] is not successful, current status is: "
                                    + rl_result["status"])

                        if get_rl_result:
                            break

            return rl_return

        return inner

    def stop(self):
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

    if mp_queue_error is None:
        logging.error("Scheduler: An error multiprocessing queue is \
        needed for monitor scheduler.")
        return

    try:
        logging.try_init_root(logging.INFO)
        scheduler = Scheduler()
        scheduler.config(max_number_of_running_task=max_number_of_running_task,
                         max_number_of_tasks=max_number_of_tasks,
                         task_config_template_path=task_config_template_path,
                         dijob_project_name=dijob_project_name,
                         k8s_dijob_yaml_file_path=k8s_dijob_yaml_file_path,
                         k8s_remote_project_path=k8s_remote_project_path,
                         mode=mode,
                         time_out=time_out,
                         mp_queue_input=mp_queue_input,
                         mp_queue_output=mp_queue_output)

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

    if mode == "local":
        multiprocessing.set_start_method("spawn")

    scheduler = Scheduler()
    scheduler.config(task_config_template_path=task_config_template_path,
                     dijob_project_name=dijob_project_name,
                     max_number_of_running_task=max_number_of_running_task,
                     max_number_of_tasks=max_number_of_tasks,
                     mode=mode,
                     time_out=time_out,
                     k8s_dijob_yaml_file_path=k8s_dijob_yaml_file_path,
                     k8s_remote_project_path=k8s_remote_project_path)

    mp_queue_input, mp_queue_output = scheduler.get_mp_queues()
    mp_queue_error = multiprocessing.Queue()

    p = multiprocessing.Process(target=scheduler_main,
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
                                ))
    p.start()

    scheduler.monitor_thread = threading.Thread(
        target=monitor_scheduler_thead_main, args=(mp_queue_error, ))
    scheduler.monitor_thread.start()

    return scheduler


def run_scheduler_local(
        task_config_template_path,
        dijob_project_name=None,
        max_number_of_running_task=2,
        max_number_of_tasks=100000,
        time_out=None,
) -> Scheduler:

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
        k8s_dijob_yaml_file_path=None,
        time_out=None,
) -> Scheduler:

    k8s_remote_project_path = None
    dijob_project_name = None
    max_number_of_running_task = 10000
    max_number_of_tasks = 100000

    with open(k8s_dijob_yaml_file_path, mode="r", encoding="UTF-8") as f:

        ryaml = YAML()
        ryaml_content = list(ryaml.load_all(f))

    for content in ryaml_content:
        if content["kind"] == "DIJob":
            if "projectPath" not in content["spec"]:
                logging.error(
                    "Scheduler: k8s remote project path is not defined in yaml file, of which should be assigned in 'spec.projectPath'."
                )
                return
            dijob_project_name = content["metadata"]["name"]
            k8s_remote_project_path = content["spec"]["projectPath"]

    if dijob_project_name is None:
        logging.error("Scheduler: no k8s project name is assigned.")
        return
    if k8s_remote_project_path is None:
        logging.error("Scheduler: no k8s remote project path is assigned.")
        return

    return run_scheduler(task_config_template_path=task_config_template_path,
                         dijob_project_name=dijob_project_name,
                         max_number_of_running_task=max_number_of_running_task,
                         max_number_of_tasks=max_number_of_tasks,
                         mode="k8s",
                         time_out=time_out,
                         k8s_dijob_yaml_file_path=k8s_dijob_yaml_file_path,
                         k8s_remote_project_path=k8s_remote_project_path)
