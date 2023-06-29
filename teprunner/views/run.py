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
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from teprunner.models import Case, CaseResult, PlanResult
from teprunner.serializers import CaseResultSerializer, PlanResultSerializer
from teprunnerbackend.settings import BASE_DIR


def fixture_filename(fixture_id):
    return f"fixture_{str(fixture_id)}.py"


def case_filename(case_id):
    return f"test_{str(case_id)}.py"


class ProjectPath:
    sandbox_path = os.path.join(BASE_DIR, "teprunner", "sandbox")

    def __init__(self, project_id):
        # 初始化目录文件
        if not os.path.exists(self.sandbox_path):
            os.mkdir(self.sandbox_path)

        self.project_id = project_id
        self.sandbox_project_path = os.path.join(self.sandbox_path, f"project_{str(project_id)}")  # 项目临时目录名称


def write_conf_yaml(project_dir, env_name):
    # conf.yaml
    filepath = os.path.join(project_dir, "resources", "tep.yaml")
    f = open(filepath, "r", encoding="utf-8")
    conf = yaml.load(f.read(), Loader=yaml.FullLoader)
    f.close()
    conf["env"] = env_name
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(conf, f)


def pull_file_from_database(project_id, project_dir, run_env):
    # 从数据库拉代码写入文件
    fixtures_dir = os.path.join(project_dir, "fixtures")
    write_conf_yaml(project_dir, run_env)


def find_case(tests_dir, cases):
    # 从数据库拉代码写入文件
    for case in cases:
        filepath = case.filename
        yield case.id, filepath


def delete_case_result(case_id, run_user_nickname):
    # 删除历史记录
    try:
        instance = CaseResult.objects.get(case_id=case_id, run_user_nickname=run_user_nickname)
        instance.delete()
    except ObjectDoesNotExist:
        pass


def delete_plan_result(plan_id, case_id):
    try:
        instance = PlanResult.objects.get(plan_id=plan_id, case_id=case_id)
        instance.delete()
    except ObjectDoesNotExist:
        pass


def pytest_subprocess(cmd, case_id, run_env, run_user_nickname, plan_id=None):
    # 执行pytest命令
    output = subprocess.getoutput(cmd)
    return output, cmd, case_id, run_env, run_user_nickname, plan_id


def save_case_result(pytest_result):
    # 保存用例结果
    output, cmd, case_id, run_env, run_user_nickname, plan_id = pytest_result.result()
    summary = output.split("\n")[-1]
    elapsed = 0
    try:
        result, elapsed, = summary.strip("=").strip().split(" in ")
        elapsed = elapsed.split(" ")[0]
    except:
        result = "执行失败"
    if not plan_id:  # 运行用例
        data = {
            "caseId": case_id,
            "result": result,
            "elapsed": elapsed,
            "output": output,
            "runEnv": run_env,
            "runUserNickname": run_user_nickname
        }
        try:
            instance = CaseResult.objects.get(case_id=case_id, run_user_nickname=run_user_nickname)
            serializer = CaseResultSerializer(data=data, instance=instance)  # 更新
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ObjectDoesNotExist:  # 新增
            serializer = CaseResultSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
    else:  # 运行计划
        data = {
            "planId": plan_id,
            "caseId": case_id,
            "result": result,
            "elapsed": elapsed,
            "output": output,
            "runEnv": run_env,
            "runUserNickname": run_user_nickname
        }
        try:
            instance = PlanResult.objects.get(plan_id=plan_id, case_id=case_id, run_user_nickname=run_user_nickname)
            serializer = PlanResultSerializer(data=data, instance=instance)  # 更新
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ObjectDoesNotExist:  # 新增
            serializer = PlanResultSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()


@api_view(['POST'])
def run_case(request, *args, **kwargs):
    case_id = kwargs["pk"]  # 用例id
    run_env = request.data.get("runEnv")  # 运行环境
    run_user_nickname = request.data.get("runUserNickname")  # 运行人
    case = Case.objects.get(id=case_id)
    project_id = case.project_id  # 项目id
    request_jwt = request.headers.get("Authorization").replace("Bearer ", "")
    request_jwt_decoded = jwt.decode(request_jwt, verify=False, algorithms=['HS512'])
    user_id = request_jwt_decoded["user_id"]  # 用户id
    p = ProjectPath(project_id)  # 项目目录文件

    if not os.path.exists(p.sandbox_project_path):
        os.chdir(p.sandbox_path)
        # todo clone

    # todo 激活环境tep.yaml
    thread_pool = ThreadPoolExecutor()  # 多线程
    tests_dir = os.path.join(p.sandbox_project_path, "tests")
    for case_to_run in find_case(tests_dir, [case]):  # [case]单个用例
        case_id, filepath = case_to_run
        delete_case_result(case_id, run_user_nickname)  # 删除历史记录
        os.chdir(tests_dir)
        cmd = rf"pytest -s {filepath}"  # pytest命令
        args = (pytest_subprocess, cmd, case_id, run_env, run_user_nickname)  # 运行参数
        thread_pool.submit(*args).add_done_callback(save_case_result)  # 多线程调用与回调
        return Response({"msg": "用例运行成功"}, status=status.HTTP_200_OK)

def run_plan_engine(project_id, plan_id, run_env, run_user_nickname, user_id):
    p = ProjectPath(project_id, run_env, user_id)

    # if not os.path.exists(p.project_temp_dir()):
    #     os.chdir(p.projects_root)
    #     create_scaffold(p.project_temp_name)
    # pull_file_from_database(project_id, p.project_temp_dir(), run_env)
    #
    # plan_case_ids = [plan_case.case_id for plan_case in PlanCase.objects.filter(plan_id=plan_id)]
    # case_list = Case.objects.filter(Q(id__in=plan_case_ids))
    # thread_pool = ThreadPoolExecutor()
    # tests_dir = os.path.join(p.project_temp_dir(), "tests")
    # for newest_case in pull_case_files(tests_dir, case_list):
    #     case_id, filepath = newest_case
    #     delete_plan_result(plan_id, case_id)
    #     os.chdir(tests_dir)
    #     cmd = rf"pytest -s {filepath}"
    #     args = (pytest_subprocess, cmd, case_id, run_env, run_user_nickname, plan_id)
    #     thread_pool.submit(*args).add_done_callback(save_case_result)


@api_view(['POST'])
def run_plan(request, *args, **kwargs):
    plan_id = kwargs["plan_id"]
    # run_env = request.data.get("runEnv")
    # run_user_nickname = request.data.get("runUserNickname")
    # project_id = Plan.objects.get(id=plan_id).project_id
    # request_jwt = request.headers.get("Authorization").replace("Bearer ", "")
    # request_jwt_decoded = jwt.decode(request_jwt, verify=False, algorithms=['HS512'])
    # user_id = request_jwt_decoded["user_id"]
    # run_plan_engine(project_id, plan_id, run_env, run_user_nickname, user_id)

    return Response({"msg": "计划运行成功"}, status=status.HTTP_200_OK)
