#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2021/3/26 11:06
@Desc    :  
"""
import os
import subprocess
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


class ProjectPath:
    def __init__(self, project_id):
        # 初始化目录文件
        if not os.path.exists(SANDBOX_PATH):
            os.mkdir(SANDBOX_PATH)

        self.project_id = project_id
        project_name = Case.objects.filter(project_id=project_id)[0].filepath.split(os.sep)[0]
        self.sandbox_project_path = os.path.join(SANDBOX_PATH, project_name)


def write_conf_yaml(project_dir, env_name):
    # conf.yaml
    filepath = os.path.join(project_dir, "resources", "tep.yaml")
    f = open(filepath, "r", encoding="utf-8")
    conf = yaml.load(f.read(), Loader=yaml.FullLoader)
    f.close()
    conf["env"] = env_name
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(conf, f)


def find_case(tests_dir, cases):
    # 数据库查找用例
    for case in cases:
        filepath = case.filename
        yield case.id, filepath


def delete_task_result(task_id, case_id):
    try:
        instance = TaskResult.objects.get(task_id=task_id, case_id=case_id)
        instance.delete()
    except ObjectDoesNotExist:
        pass


def pytest_subprocess(cmd, case_id, run_env, run_user_nickname, task_id=None):
    # 执行pytest命令
    output = subprocess.getoutput(cmd)
    return output, cmd, case_id, run_env, run_user_nickname, task_id


def save_case_result(pytest_result):
    # 保存用例结果
    output, cmd, case_id, run_env, run_user_nickname, task_id = pytest_result.result()
    summary = output.split("\n")[-1]
    elapsed = 0
    try:
        result, elapsed, = summary.strip("=").strip().split(" in ")
        elapsed = elapsed.split(" ")[0]
    except:
        result = "执行失败"
    data = {
        "taskId": task_id,
        "caseId": case_id,
        "result": result,
        "elapsed": elapsed,
        "output": output,
        "runEnv": run_env,
        "runUserNickname": run_user_nickname
    }
    try:
        instance = TaskResult.objects.get(task_id=task_id, case_id=case_id, run_user_nickname=run_user_nickname)
        serializer = TaskResultSerializer(data=data, instance=instance)  # 更新
        serializer.is_valid(raise_exception=True)
        serializer.save()
    except ObjectDoesNotExist:  # 新增
        serializer = TaskResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()


def run_task_engine(project_id, task_id, run_env, run_user_nickname):
    p = ProjectPath(project_id)

    if not os.path.exists(p.sandbox_project_path):
        os.chdir(SANDBOX_PATH)
        # todo clone

    # todo 激活环境tep.yaml
    task_case_ids = [task_case.case_id for task_case in TaskCase.objects.filter(task_id=task_id)]
    case_list = Case.objects.filter(Q(id__in=task_case_ids))
    thread_pool = ThreadPoolExecutor()
    tests_dir = os.path.join(p.sandbox_project_path, "tests")
    for case_to_run in find_case(tests_dir, case_list):
        case_id, filepath = case_to_run
        delete_task_result(task_id, case_id)
        os.chdir(tests_dir)
        cmd = rf"pytest -s {filepath}"
        args = (pytest_subprocess, cmd, case_id, run_env, run_user_nickname, task_id)
        thread_pool.submit(*args).add_done_callback(save_case_result)


@api_view(['POST'])
def run_task(request, *args, **kwargs):
    task_id = kwargs["task_id"]
    run_env = request.data.get("runEnv")
    run_user_nickname = request.data.get("runUserNickname")
    project_id = Task.objects.get(id=task_id).project_id
    request_jwt = request.headers.get("Authorization").replace("Bearer ", "")
    request_jwt_decoded = jwt.decode(request_jwt, verify=False, algorithms=['HS512'])
    user_id = request_jwt_decoded["user_id"]
    run_task_engine(project_id, task_id, run_env, run_user_nickname)

    return Response({"msg": "计划运行成功"}, status=status.HTTP_200_OK)
