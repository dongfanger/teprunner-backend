#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2021/3/17 17:20
@Desc    :  
"""
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import EnvVar
from teprunner.serializers import EnvVarSerializer


class EnvVarViewSet(ModelViewSet):
    queryset = EnvVar.objects.all()
    serializer_class = EnvVarSerializer

    def list(self, request, *args, **kwargs):
        project_id = request.GET.get("curProjectId")
        env_name = request.GET.get("curEnvName")
        queryset = EnvVar.objects.filter(Q(project_id=project_id) & Q(env_name=env_name))

        # ------------------复用代码开始--------------------
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        # ------------------复用代码结束--------------------
