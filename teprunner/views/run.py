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
from concurrent.futures.thread import ThreadPoolExecutor

import jwt
import yaml
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from teprunner.models import Fixture, EnvVar, Case, CaseResult, Project, Plan, PlanCase, PlanResult
from teprunner.serializers import CaseResultSerializer, PlanResultSerializer


def fixture_filename(fixture_id):
    return f"fixture_{str(fixture_id)}.py"


def case_filename(case_id):
    return f"test_{str(case_id)}.py"


class ProjectPath:
    _views_dir = os.path.dirname(os.path.abspath(__file__))
    _teprunner_dir = os.path.dirname(_views_dir)
    projects_root = os.path.join(_teprunner_dir, "projects")
    init_filepath = os.path.join(projects_root, "__init__.py")
    export_dir = os.path.join(projects_root, "export")

    def __init__(self, project_id, env_name, user_id):
        if not os.path.exists(self.projects_root):
            os.mkdir(self.projects_root)
        if not os.path.exists(self.init_filepath):
            with open(self.init_filepath, "w"):
                pass
        if not os.path.exists(self.export_dir):
            os.mkdir(self.export_dir)

        self.project_id = project_id
        self.project_temp_name = f"project_{str(project_id)}_{env_name}_{user_id}"
        self.export_filename = f"{Project.objects.get(id=project_id).name}_{env_name}.zip"

    def project_temp_dir(self):
        return os.path.join(self.projects_root, self.project_temp_name)

    def export_temp_dir(self):
        return os.path.join(self.export_dir, self.project_temp_name)


def startproject(project_name):
    subprocess.call(f"tep startproject {project_name}", shell=True)


def env_vars_code(mapping, definition):
    code = f"""#!/usr/bin/python
# encoding=utf-8


from tep.dao import mysql_engine
from tep.fixture import *


@pytest.fixture(scope="session")
def env_vars(config):
    class Clazz(TepVars):
        env = config["env"]
        mapping = {mapping}
        {definition}

    return Clazz()
"""
    return code


def write_fixture_env_vars_file(project_id, fixtures_dir):
    env_vars = EnvVar.objects.filter(project_id=project_id)
    mapping = {}
    props = []
    for env_var in env_vars:
        name = env_var.name
        value = env_var.value
        env_name = env_var.env_name
        mapping.setdefault(env_name, {name: value})[name] = value
        prop = f'{name} = mapping[env]["{name}"]'
        if prop not in props:
            props.append(prop)

    definition = ("\n" + " " * 8).join(props)
    filepath = os.path.join(fixtures_dir, "fixture_env_vars.py")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(env_vars_code(mapping, definition))


def write_fixture_file(project_id, fixtures_dir):
    fixtures = Fixture.objects.filter(project_id=project_id)
    for fixture in fixtures:
        filepath = os.path.join(fixtures_dir, fixture_filename(fixture.id))
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(fixture.code)


def write_case_file(tests_dir, case_id, code):
    filepath = os.path.join(tests_dir, case_filename(case_id))
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    return filepath


def write_conf_yaml(project_dir, env_name):
    filepath = os.path.join(project_dir, "conf.yaml")
    f = open(filepath, "r", encoding="utf-8")
    conf = yaml.load(f.read(), Loader=yaml.FullLoader)
    f.close()
    conf["env"] = env_name
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(conf, f)


def clean_fixtures_dir(fixtures_dir):
    for filename in os.listdir(fixtures_dir):
        if filename != "__init__.py":
            path = os.path.join(fixtures_dir, filename)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)


def clean_tests_dir(tests_dir):
    for filename in os.listdir(tests_dir):
        if filename != "__init__.py":
            path = os.path.join(tests_dir, filename)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)


def pull_tep_files(project_id, project_dir, run_env):
    fixtures_dir = os.path.join(project_dir, "fixtures")
    write_fixture_env_vars_file(project_id, fixtures_dir)
    write_fixture_file(project_id, fixtures_dir)
    write_conf_yaml(project_dir, run_env)


def pull_case_files(tests_dir, cases):
    for case in cases:
        filepath = write_case_file(tests_dir, case.id, case.code)
        yield case.id, filepath


def delete_case_result(case_id, run_user_nickname):
    try:
        instance = CaseResult.objects.get(case_id=case_id, run_user_nickname=run_user_nickname)
        instance.delete()
    except ObjectDoesNotExist:
        pass


def delete_plan_result(plan_id, case_id, run_user_nickname):
    try:
        instance = PlanResult.objects.get(plan_id=plan_id, case_id=case_id, run_user_nickname=run_user_nickname)
        instance.delete()
    except ObjectDoesNotExist:
        pass


def pytest_subprocess(cmd, case_id, run_env, run_user_nickname, plan_id=None):
    output = subprocess.getoutput(cmd)
    return output, cmd, case_id, run_env, run_user_nickname, plan_id


def save_case_result(pytest_result):
    output, cmd, case_id, run_env, run_user_nickname, plan_id = pytest_result.result()
    summary = output.split("\n")[-1]
    result, elapsed, = summary.strip("=").strip().split(" in ")
    if not plan_id:
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
            serializer = CaseResultSerializer(data=data, instance=instance)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ObjectDoesNotExist:
            serializer = CaseResultSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
    else:
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
            serializer = PlanResultSerializer(data=data, instance=instance)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ObjectDoesNotExist:
            serializer = PlanResultSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()


@api_view(['POST'])
def run_case(request, *args, **kwargs):
    case_id = kwargs["pk"]
    run_env = request.data.get("runEnv")
    run_user_nickname = request.data.get("runUserNickname")
    case = Case.objects.get(id=case_id)
    project_id = case.project_id
    request_jwt = request.headers.get("Authorization").replace("Bearer ", "")
    request_jwt_decoded = jwt.decode(request_jwt, verify=False, algorithms=['HS512'])
    user_id = request_jwt_decoded["user_id"]
    p = ProjectPath(project_id, run_env, user_id)

    if not os.path.exists(p.project_temp_dir()):
        os.chdir(p.projects_root)
        startproject(p.project_temp_name)
    clean_fixtures_dir(os.path.join(p.project_temp_dir(), "fixtures"))
    clean_tests_dir(os.path.join(p.project_temp_dir(), "tests"))
    pull_tep_files(project_id, p.project_temp_dir(), run_env)

    thread_pool = ThreadPoolExecutor()
    tests_dir = os.path.join(p.project_temp_dir(), "tests")
    for newest_case in pull_case_files(tests_dir, [case]):
        case_id, filepath = newest_case
        delete_case_result(case_id, run_user_nickname)
        os.chdir(tests_dir)
        cmd = rf"pytest -s {filepath}"
        args = (pytest_subprocess, cmd, case_id, run_env, run_user_nickname)
        thread_pool.submit(*args).add_done_callback(save_case_result)
        return Response({"msg": "用例运行成功"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def run_plan(request, *args, **kwargs):
    plan_id = kwargs["plan_id"]
    run_env = request.data.get("runEnv")
    run_user_nickname = request.data.get("runUserNickname")
    project_id = Plan.objects.get(id=plan_id).project_id
    request_jwt = request.headers.get("Authorization").replace("Bearer ", "")
    request_jwt_decoded = jwt.decode(request_jwt, verify=False, algorithms=['HS512'])
    user_id = request_jwt_decoded["user_id"]
    p = ProjectPath(project_id, run_env, user_id)

    if not os.path.exists(p.project_temp_dir()):
        os.chdir(p.projects_root)
        startproject(p.project_temp_name)
    clean_fixtures_dir(os.path.join(p.project_temp_dir(), "fixtures"))
    clean_tests_dir(os.path.join(p.project_temp_dir(), "tests"))
    pull_tep_files(project_id, p.project_temp_dir(), run_env)

    plan_case_ids = [plan_case.case_id for plan_case in PlanCase.objects.filter(plan_id=plan_id)]
    case_list = Case.objects.filter(Q(id__in=plan_case_ids))
    thread_pool = ThreadPoolExecutor()
    tests_dir = os.path.join(p.project_temp_dir(), "tests")
    for newest_case in pull_case_files(tests_dir, case_list):
        case_id, filepath = newest_case
        delete_plan_result(plan_id, case_id, run_user_nickname)
        os.chdir(tests_dir)
        cmd = rf"pytest -s {filepath}"
        args = (pytest_subprocess, cmd, case_id, run_env, run_user_nickname, plan_id)
        thread_pool.submit(*args).add_done_callback(save_case_result)

    return Response({"msg": "计划运行成功"}, status=status.HTTP_200_OK)
