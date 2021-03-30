# Create your views here.
import os
import shutil
import zipfile

import jwt
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import Project
from teprunner.serializers import ProjectSerializer
from teprunner.views.run import ProjectPath, startproject, write_conf_yaml, pull_tep_files, clean_fixtures_dir, \
    clean_tests_dir
from user.models import User


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminUser]


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
