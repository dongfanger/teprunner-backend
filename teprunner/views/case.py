#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2021/1/21 14:20
@Desc    :  
"""
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import Case, CaseResult
from teprunner.serializers import CaseSerializer, CaseResultSerializer, CaseListSerializer
from user.pagination import CustomPagination


class CaseViewSet(ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer

    def list(self, request, *args, **kwargs):
        project_id = request.GET.get("projectId")
        query = Q(project_id=project_id)
        case_id = request.GET.get("id")
        if case_id:
            query &= Q(id=case_id)
        desc = request.GET.get("desc")
        if desc:
            query &= Q(desc__icontains=desc)
        api = request.GET.get("api")
        if api:
            query &= Q(code__icontains=api)
        queryset = Case.objects.filter(query).order_by('-id')
        cp = CustomPagination()
        page = cp.paginate_queryset(queryset, request=request)
        if page is not None:
            serializer = CaseListSerializer(page, many=True)
            return cp.get_paginated_response(serializer.data)

    def update(self, request, *args, **kwargs):
        case_id = kwargs["pk"]
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        request.data["creatorNickname"] = Case.objects.get(id=case_id).creator_nickname
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


@api_view(['GET'])
def case_result(request, *args, **kwargs):
    case_id = kwargs["pk"]
    instance = CaseResult.objects.get(case_id=case_id)
    serializer = CaseResultSerializer(instance=instance)
    return Response(serializer.data)


@api_view(['POST'])
def copy_case(request, *args, **kwargs):
    case_id = kwargs["pk"]
    case = Case.objects.get(id=case_id)
    new_case = {
        "desc": case.desc + "--复制",
        "code": case.code,
        "creatorNickname": request.data.get("creatorNickname"),
        "projectId": case.project_id
    }
    serializer = CaseSerializer(data=new_case)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"msg": "用例复制成功"}, status=status.HTTP_200_OK)
