#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2021/2/7 9:35
@Desc    :  
"""
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import Task, TaskCase, Case, TaskResult
from teprunner.serializers import TaskSerializer, TaskCaseSerializer, TaskResultSerializer, CaseSerializer
from teprunner.views.run import run_task_engine
from teprunner.views.schedule import scheduler
from user.pagination import CustomPagination


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def create(self, request, *args, **kwargs):
        name = request.data.get("name")
        try:
            task = Task.objects.get(name=name)
            return Response(f"task {task.name} existed", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            task = Task.objects.get(name=request.data.get("name"))
            project_id = request.data.get("projectId")
            task_run_env = request.data.get("taskRunEnv")
            task_status = request.data.get("taskStatus")
            task_crontab = request.data.get("taskCrontab")
            task_added = ""
            if task_status == "1":
                run_user_nickname = "定时任务"
                user_id = "task"
                task_added = scheduler.add_job(func=run_task_engine,
                                               trigger=CronTrigger.from_crontab(task_crontab),
                                               id=str(task.id),
                                               args=[project_id, task.id, task_run_env, run_user_nickname, user_id],
                                               max_instances=1,
                                               replace_existing=True)
            data = serializer.data
            data["taskAdded"] = str(task_added)
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        name = request.data.get("name")
        task_id = kwargs["pk"]
        try:
            task = Task.objects.get(name=name)
            if task_id != task.id:
                return Response(f"task {task.name} existed ", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist:
            pass

        project_id = request.data.get("projectId")
        task_run_env = request.data.get("taskRunEnv")
        task_status = request.data.get("taskStatus")
        task_crontab = request.data.get("taskCrontab")
        task_updated = ""

        if task_status == "1":
            run_user_nickname = "定时任务"
            user_id = "task"
            task_updated = scheduler.add_job(func=run_task_engine,
                                             trigger=CronTrigger.from_crontab(task_crontab),
                                             id=str(task_id),
                                             args=[project_id, task_id, task_run_env, run_user_nickname, user_id],
                                             max_instances=1,
                                             replace_existing=True)
        if task_status == "0":
            try:
                task_updated = scheduler.remove_job(str(task_id))
            except JobLookupError:
                task_updated = "task removed"

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        data = serializer.data
        data["taskUpdated"] = str(task_updated)
        return Response(data)

    def list(self, request, *args, **kwargs):
        project_id = request.GET.get("projectId")
        query = Q(project_id=project_id)
        task_name = request.GET.get("name")
        if task_name:
            query &= Q(name__icontains=task_name)
        queryset = Task.objects.filter(query).order_by('-id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        task_id = kwargs["pk"]
        task_case = TaskCase.objects.filter(task_id=task_id)
        if task_case:
            return Response({"msg": "请先删除关联测试用例"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            try:
                scheduler.remove_job(str(task_id))
            except JobLookupError:
                pass
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)


class TaskCaseView(ModelViewSet):
    queryset = TaskCase.objects.all()
    serializer_class = TaskCaseSerializer

    def list(self, request, *args, **kwargs):
        task_id = kwargs["task_id"]
        query = Q(task_id=task_id)
        keyword = request.GET.get("keyword")
        if keyword:
            try:
                int(keyword)
                case_id_query = Q(case_id=keyword)
            except ValueError:
                case_id_query = Q()
            case_desc_query = Q(case_id__in=[case.id for case in Case.objects.filter(Q(desc__icontains=keyword))])
            query &= (case_id_query | case_desc_query)
        queryset = TaskCase.objects.filter(query).order_by("-case_id")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def add(self, request, *args, **kwargs):
        task_id = kwargs["task_id"]
        case_ids = request.data.get("caseIds")
        for case_id in case_ids:
            try:
                TaskCase.objects.get(task_id=task_id, case_id=case_id)
            except ObjectDoesNotExist:
                data = {
                    "taskId": task_id,
                    "caseId": case_id
                }
                serializer = TaskCaseSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return Response({"caseIds": case_ids}, status=status.HTTP_201_CREATED)

    def remove(self, request, *args, **kwargs):
        task_id = kwargs["task_id"]
        case_id = kwargs["case_id"]
        task_case = TaskCase.objects.get(task_id=task_id, case_id=case_id)
        task_case.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def cases(request, *args, **kwargs):
    project_id = request.GET.get("projectId")
    case_list = Case.objects.filter(project_id=project_id)
    cp = CustomPagination()
    page = cp.paginate_queryset(case_list, request=request)
    if page is not None:
        serializer = CaseSerializer(page, many=True)
        return cp.get_paginated_response(serializer.data)

@api_view(['GET'])
def result(request, *args, **kwargs):
    search_type = request.GET.get("searchType")
    task_id = kwargs["task_id"]
    query = Q(task_id=task_id)
    if search_type == "passed":
        query &= Q(result__icontains="passed")
        query &= ~Q(result__icontains="failed")
        query &= ~Q(result__icontains="error")
    elif search_type == "failed":
        query &= Q(result__icontains="failed")
        query &= ~Q(result__icontains="error")
    elif search_type == "error":
        query &= Q(result__icontains="error")
    task_result = TaskResult.objects.filter(query)
    cp = CustomPagination()
    page = cp.paginate_queryset(task_result, request=request)
    if page is not None:
        serializer = TaskResultSerializer(page, many=True)
        return cp.get_paginated_response(serializer.data)


@api_view(['GET'])
def case_result(request, *args, **kwargs):
    task_id = kwargs["task_id"]
    case_id = kwargs["case_id"]
    case = Case.objects.get(id=case_id)
    task_result = TaskResult.objects.filter(task_id=task_id, case_id=case_id).order_by('-run_time')
    task_result = task_result[0]
    data = {
        "taskId": task_id,
        "caseId": case_id,
        "caseDesc": case.desc,
        "caseCreatorNickname": case.creator_nickname,
        "result": task_result.result,
        "elapsed": task_result.elapsed,
        "output": task_result.output,
        "runEnv": task_result.run_env,
        "runUserNickname": task_result.run_user_nickname,
        "runTime": task_result.run_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return Response(data, status=status.HTTP_200_OK)
