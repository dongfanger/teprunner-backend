#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2021/2/7 9:35
@Desc    :  
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import Plan, PlanCase, Case, PlanResult
from teprunner.serializers import PlanSerializer, PlanCaseSerializer, PlanResultSerializer
from user.pagination import CustomPagination


class PlanViewSet(ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def list(self, request, *args, **kwargs):
        project_id = request.GET.get("projectId")
        query = Q(project_id=project_id)
        plan_name = request.GET.get("name")
        if plan_name:
            query &= Q(name__icontains=plan_name)
        queryset = Plan.objects.filter(query).order_by('-id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        plan_id = kwargs["pk"]
        plan_case = PlanCase.objects.filter(plan_id=plan_id)
        if plan_case:
            return Response({"msg": "请先删除关联测试用例"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class PlanCaseView(ModelViewSet):
    queryset = PlanCase.objects.all()
    serializer_class = PlanCaseSerializer

    def list(self, request, *args, **kwargs):
        plan_id = kwargs["plan_id"]
        query = Q(plan_id=plan_id)
        keyword = request.GET.get("keyword")
        if keyword:
            try:
                int(keyword)
                case_id_query = Q(case_id=keyword)
            except ValueError:
                case_id_query = Q()
            case_desc_query = Q(case_id__in=[case.id for case in Case.objects.filter(Q(desc__icontains=keyword))])
            query &= (case_id_query | case_desc_query)
        queryset = PlanCase.objects.filter(query).order_by("-case_id")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def add(self, request, *args, **kwargs):
        plan_id = kwargs["plan_id"]
        case_ids = request.data.get("caseIds")
        for case_id in case_ids:
            try:
                PlanCase.objects.get(plan_id=plan_id, case_id=case_id)
            except ObjectDoesNotExist:
                data = {
                    "planId": plan_id,
                    "caseId": case_id
                }
                serializer = PlanCaseSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return Response({"caseIds": case_ids}, status=status.HTTP_201_CREATED)

    def remove(self, request, *args, **kwargs):
        plan_id = kwargs["plan_id"]
        case_id = kwargs["case_id"]
        plan_case = PlanCase.objects.get(plan_id=plan_id, case_id=case_id)
        plan_case.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def result(request, *args, **kwargs):
    search_type = request.GET.get("searchType")
    plan_id = kwargs["plan_id"]
    query = Q(plan_id=plan_id)
    if search_type == "passed":
        query &= Q(result__icontains="passed")
        query &= ~Q(result__icontains="failed")
        query &= ~Q(result__icontains="error")
    elif search_type == "failed":
        query &= Q(result__icontains="failed")
        query &= ~Q(result__icontains="error")
    elif search_type == "error":
        query &= Q(result__icontains="error")
    plan_result = PlanResult.objects.filter(query)
    cp = CustomPagination()
    page = cp.paginate_queryset(plan_result, request=request)
    if page is not None:
        serializer = PlanResultSerializer(page, many=True)
        return cp.get_paginated_response(serializer.data)


@api_view(['GET'])
def case_result(request, *args, **kwargs):
    plan_id = kwargs["plan_id"]
    case_id = kwargs["case_id"]
    case = Case.objects.get(id=case_id)
    plan_result = PlanResult.objects.get(plan_id=plan_id, case_id=case_id)
    data = {
        "planId": plan_id,
        "caseId": case_id,
        "caseDesc": case.desc,
        "caseCreatorNickname": case.creator_nickname,
        "result": plan_result.result,
        "elapsed": plan_result.elapsed,
        "output": plan_result.output,
        "runEnv": plan_result.run_env,
        "runUserNickname": plan_result.run_user_nickname,
        "runTime": plan_result.run_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return Response(data, status=status.HTTP_200_OK)
