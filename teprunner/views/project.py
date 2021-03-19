# Create your views here.

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import Project
from teprunner.serializers import ProjectSerializer


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
