# Create your views here.
import os
import shutil
import zipfile

import jwt
from django.core.exceptions import ObjectDoesNotExist
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import Project
from teprunner.serializers import ProjectSerializer, EnvVarSerializer, FixtureSerializer
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
