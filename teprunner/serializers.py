#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/12/24 14:50
@Desc    :  
"""
import os.path

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from teprunner.models import Project, Case, Task, TaskCase, TaskResult
from teprunnerbackend.settings import SANDBOX_PATH


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    envConfig = serializers.CharField(source="env_config")
    gitRepository = serializers.CharField(source="git_repository", required=False, allow_blank=True)
    gitBranch = serializers.CharField(source="git_branch", required=False, allow_blank=True)
    lastSyncTime = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Project
        fields = ["id", "name", "envConfig", "gitRepository", "gitBranch", "lastSyncTime"]

    def get_lastSyncTime(self, instance):
        return instance.last_sync_time.strftime("%Y-%m-%d %H:%M:%S") if instance.last_sync_time else ""


class CaseSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    creatorNickname = serializers.CharField(source="creator_nickname", required=False)
    projectId = serializers.CharField(source="project_id")

    class Meta:
        model = Case
        fields = ["id", "desc", "creatorNickname", "projectId", "filename", "filepath"]

class TaskSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    projectId = serializers.CharField(source="project_id")
    taskStatus = serializers.CharField(source="task_status")
    taskCrontab = serializers.CharField(source="task_crontab", required=False, allow_blank=True)
    taskRunEnv = serializers.CharField(source="task_run_env", required=False, allow_blank=True)

    caseNum = serializers.SerializerMethodField(required=False)
    passedNum = serializers.SerializerMethodField(required=False)
    failedNum = serializers.SerializerMethodField(required=False)
    errorNum = serializers.SerializerMethodField(required=False)
    elapsed = serializers.SerializerMethodField(required=False)
    runEnv = serializers.SerializerMethodField(required=False)
    runUserNickname = serializers.SerializerMethodField(required=False)
    runTime = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Task
        fields = ["id", "name", "projectId", "taskStatus", "taskCrontab", "taskRunEnv",
                  "caseNum", "passedNum", "failedNum", "errorNum", "elapsed", "runEnv", "runUserNickname", "runTime"]

    def get_caseNum(self, instance):
        task_id = instance.id
        try:
            case_num = len(TaskCase.objects.filter(task_id=task_id))
        except ObjectDoesNotExist:
            return ""
        return str(case_num)

    def get_passedNum(self, instance):
        task_id = instance.id
        try:
            passed_num = 0
            for task_result in TaskResult.objects.filter(task_id=task_id):
                if ("passed" in task_result.result
                        and "failed" not in task_result.result
                        and "error" not in task_result.result):
                    passed_num += 1
        except ObjectDoesNotExist:
            return ""
        return str(passed_num)

    def get_failedNum(self, instance):
        task_id = instance.id
        try:
            failed_num = 0
            for task_result in TaskResult.objects.filter(task_id=task_id):
                if "failed" in task_result.result and "error" not in task_result.result:
                    failed_num += 1
        except ObjectDoesNotExist:
            return ""
        return str(failed_num)

    def get_errorNum(self, instance):
        task_id = instance.id
        try:
            error_num = 0
            for task_result in TaskResult.objects.filter(task_id=task_id):
                if "error" in task_result.result:
                    error_num += 1
        except ObjectDoesNotExist:
            return ""
        return str(error_num)

    def get_elapsed(self, instance):
        task_id = instance.id
        try:
            total_elapsed = 0
            for task_result in TaskResult.objects.filter(task_id=task_id):
                total_elapsed += float(task_result.elapsed.replace("s", ""))
        except ObjectDoesNotExist:
            return ""
        return str(total_elapsed)[:4] + "s"

    def get_runEnv(self, instance):
        task_id = instance.id
        try:
            task_results = TaskResult.objects.filter(task_id=task_id)
        except ObjectDoesNotExist:
            return ""
        run_env = ""
        if task_results:
            run_env = task_results[0].run_env
        return run_env

    def get_runUserNickname(self, instance):
        task_id = instance.id
        try:
            task_results = TaskResult.objects.filter(task_id=task_id)
        except ObjectDoesNotExist:
            return ""
        run_user_nickname = ""
        if task_results:
            run_user_nickname = task_results[0].run_user_nickname
        return run_user_nickname

    def get_runTime(self, instance):
        task_id = instance.id
        try:
            task_results = TaskResult.objects.filter(task_id=task_id)
        except ObjectDoesNotExist:
            return ""
        run_time = ""
        if task_results:
            run_time = task_results.order_by('run_time')[0].run_time.strftime("%Y-%m-%d %H:%M:%S")
        return run_time


class TaskCaseSerializer(serializers.ModelSerializer):
    taskId = serializers.CharField(source="task_id")
    caseId = serializers.CharField(source="case_id")
    caseDesc = serializers.SerializerMethodField(required=False)
    caseCreatorNickname = serializers.SerializerMethodField(required=False)

    class Meta:
        model = TaskCase

        fields = ["taskId", "caseId", "caseDesc", "caseCreatorNickname"]

    def get_caseDesc(self, instance):
        task_case_id = instance.id
        case_id = TaskCase.objects.get(id=task_case_id).case_id
        return Case.objects.get(id=case_id).desc

    def get_caseCreatorNickname(self, instance):
        task_case_id = instance.id
        case_id = TaskCase.objects.get(id=task_case_id).case_id
        return Case.objects.get(id=case_id).creator_nickname


class TaskResultSerializer(serializers.ModelSerializer):
    taskId = serializers.CharField(source="task_id")
    caseId = serializers.CharField(source="case_id")
    caseDesc = serializers.SerializerMethodField(required=False)
    caseCreatorNickname = serializers.SerializerMethodField(required=False)
    runEnv = serializers.CharField(source="run_env")
    runUserNickname = serializers.CharField(source="run_user_nickname")
    runTime = serializers.SerializerMethodField()

    class Meta:
        model = TaskResult
        fields = ["taskId", "caseId", "caseDesc", "caseCreatorNickname",
                  "result", "elapsed", "output", "runEnv", "runUserNickname", "runTime"]

    def get_caseDesc(self, instance):
        return Case.objects.get(id=instance.case_id).desc

    def get_caseCreatorNickname(self, instance):
        return Case.objects.get(id=instance.case_id).creator_nickname

    def get_runTime(self, instance):
        return TaskResult.objects.get(id=instance.id).run_time.strftime("%Y-%m-%d %H:%M:%S")

    def to_representation(self, obj):
        ret = super(TaskResultSerializer, self).to_representation(obj)
        ret.pop('output')
        return ret
