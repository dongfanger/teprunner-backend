#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2021/3/26 11:06
@Desc    :  
"""
import os
import shutil
import subprocess
import time
from concurrent.futures.thread import ThreadPoolExecutor

import jwt
import yaml
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from teprunner.models import Case, TaskResult, Task, TaskCase
from teprunner.serializers import TaskResultSerializer
from teprunnerbackend.settings import SANDBOX_PATH


class TaskContext:
    def __init__(self, project_id):
        if not os.path.exists(SANDBOX_PATH):
            os.mkdir(SANDBOX_PATH)

        self.project_id = project_id
        self.project_name = Case.objects.filter(project_id=project_id)[0].filepath.split(os.sep)[0]

        self.current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
        self.case_count = 0
        self.case_num = None
        self.task_id = None
        self.run_env = ""
        self.run_user_id = None
        self.container_task_path = ""


def write_conf_yaml(project_dir, env_name):
    # conf.yaml
    filepath = os.path.join(project_dir, "resources", "tep.yaml")
    f = open(filepath, "r", encoding="utf-8")
    conf = yaml.load(f.read(), Loader=yaml.FullLoader)
    f.close()
    conf["env"] = env_name
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(conf, f)


def find_case(cases):
    # 数据库查找用例
    for case in cases:
        filepath = case.filepath
        yield case.id, filepath


def find_files_with_same_name(directory, known_file):
    known_filename = os.path.basename(known_file)
    known_file_name_without_extension = os.path.splitext(known_filename)[0]
    same_name_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename != known_filename:
                file_name = os.path.splitext(filename)[0]
                if file_name == known_file_name_without_extension:
                    file_path = os.path.join(root, filename)
                    same_name_files.append(file_path)

    return same_name_files


def pull_case(filepath, task_context):
    file_path_abs = os.path.join(SANDBOX_PATH, filepath)
    shutil.copy2(file_path_abs, task_context.container_task_path)
    same_name_files = find_files_with_same_name(os.path.dirname(file_path_abs), filepath.split(os.sep)[-1])
    if same_name_files:
        same_name_file = same_name_files[0]
        if same_name_file.endswith(".yml") or same_name_file.endswith(".yaml"):
            shutil.copy2(same_name_file, task_context.container_task_path)

    return task_context


def save_task_result(pytest_result):
    task_context = pytest_result.result()
    task_context.case_count += 1
    if task_context.case_count == task_context.case_num:
        os.chdir(task_context.container_task_path)
        report_path = os.path.join(task_context.project_name, "reports", task_context.current_time + ".html")
        cmd = f"pytest --html={os.path.join(SANDBOX_PATH, report_path)} --self-contained-html"
        subprocess.getoutput(cmd)
        data = {
            "taskId": task_context.task_id,
            "result": "执行成功",
            "runEnv": task_context.run_env,
            "runUserId": task_context.run_user_id,
            "reportPath": report_path
        }
        try:
            instance = TaskResult.objects.get(task_id=task_context.task_id, run_user_id=task_context.run_user_id)
            serializer = TaskResultSerializer(data=data, instance=instance)  # 更新
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ObjectDoesNotExist:  # 新增
            serializer = TaskResultSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()


def run_task_engine(project_id, task_id, run_env, run_user_id):
    task_context = TaskContext(project_id)
    container_path = os.path.join(SANDBOX_PATH, task_context.project_name, "container")
    if not os.path.exists(container_path):
        os.mkdir(container_path)
    container_task_path = os.path.join(container_path, f"{str(task_id)}-{task_context.current_time}")
    os.chdir(SANDBOX_PATH)
    if not os.path.exists(container_task_path):
        os.mkdir(container_task_path)
    task_context.container_task_path = container_task_path

    # todo 激活环境tep.yaml

    task_case_ids = [task_case.case_id for task_case in TaskCase.objects.filter(task_id=task_id)]
    case_list = Case.objects.filter(Q(id__in=task_case_ids))
    thread_pool = ThreadPoolExecutor()
    task_context.case_num = len(case_list)
    task_context.run_env = run_env
    task_context.run_user_id = run_user_id
    task_context.task_id = task_id
    for case_to_run in find_case(case_list):
        case_id, filepath = case_to_run
        args = (pull_case, filepath, task_context)
        thread_pool.submit(*args).add_done_callback(save_task_result)


@api_view(['POST'])
def run_task(request, *args, **kwargs):
    task_id = kwargs["task_id"]
    run_env = request.data.get("runEnv")
    project_id = Task.objects.get(id=task_id).project_id
    request_jwt = request.headers.get("Authorization").replace("Bearer ", "")
    request_jwt_decoded = jwt.decode(request_jwt, verify=False, algorithms=['HS512'])
    run_user_id = request_jwt_decoded["user_id"]
    run_task_engine(project_id, task_id, run_env, run_user_id)

    return Response({"msg": "计划运行成功"}, status=status.HTTP_200_OK)
