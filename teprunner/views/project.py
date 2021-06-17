# Create your views here.
import os
import re
import shutil
import time
import zipfile

import jwt
from django.core.exceptions import ObjectDoesNotExist
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import Project, Case
from teprunner.serializers import ProjectSerializer, EnvVarSerializer, FixtureSerializer, CaseSerializer
from teprunner.views.run import ProjectPath, startproject, pull_tep_files, clean_fixtures_dir, \
    clean_tests_dir


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        try:
            Project.objects.get(name=request.data.get("name"))
            return Response("存在同名项目", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist:
            pass
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        env_config = request.data.get("envConfig")
        env_list = env_config.replace(" ", "").split(",")
        project_id = Project.objects.get(name=request.data.get("name")).id
        for env in env_list:
            data = {
                "name": "domain",
                "value": f"https://{env}.com",
                "desc": "域名",
                "curProjectId": project_id,
                "curEnvName": env,
            }
            print(data)
            env_var_serializer = EnvVarSerializer(data=data)
            env_var_serializer.is_valid()
            env_var_serializer.save()
        code = """from tep.client import request
from tep.fixture import *


def _jwt_headers(token):
    return {"Content-Type": "application/json", "authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def login(env_vars):
    # Code your login
    logger.info("Administrator login")
    response = request(
        "post",
        url=env_vars.domain + "/api/users/login",
        headers={"Content-Type": "application/json"},
        json={
            "username": "dongfanger",
            "password": "123",
        }
    )
    assert response.status_code < 400
    response_token = jmespath.search("token", response.json())
    super_admin_id = jmespath.search("user.id", response.json())

    class Clazz:
        token = response_token
        jwt_headers = _jwt_headers(response_token)
        admin_id = super_admin_id

    return Clazz"""
        data = {
            "name": "fixture_login",
            "desc": "登录",
            "code": code,
            "creatorNickname": "管理员",
            "curProjectId": project_id
        }
        fixture_serializer = FixtureSerializer(data=data)
        fixture_serializer.is_valid()
        fixture_serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@api_view(['GET'])
def project_env(request, *args, **kwargs):
    data = {"projectEnvList": [], "curProjectEnv": {}}
    projects = Project.objects.all()
    if not projects:
        return Response(data, status=status.HTTP_200_OK)
    for project in projects:
        data["projectEnvList"].append({"projectId": str(project.id),
                                       "projectName": project.name,
                                       "envList": project.env_config.replace(" ", "").split(",")})
    data["curProjectEnv"] = {"curProjectId": str(projects[0].id),
                             "curProjectName": projects[0].name,
                             "curEnvName": projects[0].env_config.replace(" ", "").split(",")[0]}
    return Response(data, status=status.HTTP_200_OK)


def make_zip(source_dir, zip_filename):
    zip_ = zipfile.ZipFile(zip_filename, 'w')
    pre_len = len(os.path.dirname(source_dir))
    for parent, _, filenames in os.walk(source_dir):
        for filename in filenames:
            path = os.path.join(parent, filename)
            arcname = path[pre_len:].strip(os.path.sep)
            zip_.write(path, arcname)
    zip_.close()


def file_iterator(file_path, chunk_size=512):
    with open(file_path, mode='rb') as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


@api_view(['POST'])
def export_project(request, *args, **kwargs):
    project_id = kwargs["pk"]
    env_name = request.data.get("curEnvName")
    request_jwt = request.headers.get("Authorization").replace("Bearer ", "")
    request_jwt_decoded = jwt.decode(request_jwt, verify=False, algorithms=['HS512'])
    user_id = request_jwt_decoded["user_id"]

    p = ProjectPath(project_id, env_name, user_id)
    zip_filepath = os.path.join(p.export_dir, p.export_filename)
    if not os.path.exists(p.export_temp_dir()):
        os.chdir(p.export_dir)
        startproject(p.project_temp_name)
    clean_fixtures_dir(os.path.join(p.export_temp_dir(), "fixtures"))
    clean_tests_dir(os.path.join(p.export_temp_dir(), "tests"))
    pull_tep_files(project_id, p.export_temp_dir(), env_name)
    make_zip(p.export_temp_dir(), zip_filepath)
    shutil.rmtree(p.export_temp_dir())

    response = StreamingHttpResponse(file_iterator(zip_filepath))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment;filename={os.path.split(zip_filepath)[-1]}'

    return response


class GitSyncConfig:
    _views_dir = os.path.dirname(os.path.abspath(__file__))
    _teprunner_dir = os.path.dirname(_views_dir)
    projects_root = os.path.join(_teprunner_dir, "projects")
    project_id = ""
    project_name = ""
    project_git_temp_dir = os.path.join(projects_root, "project_git")
    tests_dir = ""


def file_desc_author(file):
    desc = ""
    author = ""
    line_no = 0
    with open(file, encoding="utf8") as f:
        for line in f.read().splitlines():
            if line.startswith("@Desc"):
                _, desc = line.replace(" ", "").split(":")
            if line.startswith("@Author"):
                _, author = line.replace(" ", "").split(":")
            if line_no > 10:
                break
            line_no += 1
    return desc, author


def read_git_file(filename):
    file = os.path.join(GitSyncConfig.tests_dir, filename)
    with open(file, encoding="utf8") as f:
        desc, author = file_desc_author(file)
        data = {
            "desc": desc if desc else filename,
            "code": f.read(),
            "creatorNickname": author if author else "git",
            "projectId": GitSyncConfig.project_id,
            "filename": filename,
            "source": "git"
        }
    return data


def git_pull():
    project = Project.objects.get(id=GitSyncConfig.project_id)
    repository = project.git_repository
    branch = project.git_branch
    GitSyncConfig.project_name = re.findall(r"^.*/(.*).git", repository)[0]

    if not os.path.exists(GitSyncConfig.projects_root):
        os.mkdir(GitSyncConfig.projects_root)
    if not os.path.exists(GitSyncConfig.project_git_temp_dir):
        os.mkdir(GitSyncConfig.project_git_temp_dir)
    os.chdir(GitSyncConfig.project_git_temp_dir)
    if not os.path.exists(GitSyncConfig.project_name):
        os.system(f"git clone -b {branch} {repository}")
    else:
        os.chdir(GitSyncConfig.project_name)
        os.system(f"git checkout {branch}")
        os.system("git pull")


def sync_case():
    git_filenames = []
    GitSyncConfig.tests_dir = os.path.join(GitSyncConfig.project_git_temp_dir, GitSyncConfig.project_name, "tests")
    for root, _, files in os.walk(GitSyncConfig.tests_dir):
        for file in files:
            if os.path.isfile(os.path.join(root, file)):
                if (file.startswith("test_") or file.endswith("_test")) and file.endswith(".py"):
                    filename = os.path.join(root, file).replace(GitSyncConfig.tests_dir, "").strip("\\")
                    git_filenames.append(filename)
    git_filenames = set(git_filenames)

    cases = Case.objects.filter(source="git")
    db_filenames = set(case.filename for case in cases)

    print(git_filenames)

    to_delete_cases = db_filenames - git_filenames
    to_add_cases = git_filenames - db_filenames
    to_update_cases = git_filenames & db_filenames

    for filename in to_delete_cases:
        case = Case.objects.get(filename=filename)
        case.delete()

    for filename in to_add_cases:
        data = read_git_file(filename)
        serializer = CaseSerializer(data=data)
        serializer.is_valid()
        serializer.save()

    for filename in to_update_cases:
        data = read_git_file(filename)
        case = Case.objects.get(filename=filename)
        serializer = CaseSerializer(instance=case, data=data)
        serializer.is_valid()
        serializer.save()


@api_view(['POST'])
def git_sync(request, *args, **kwargs):
    project_id = kwargs["pk"]
    GitSyncConfig.project_id = project_id
    git_pull()
    sync_case()
    project = Project.objects.get(id=project_id)
    project.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    project.save()
    return Response({"msg": "同步成功"}, status=status.HTTP_200_OK)
