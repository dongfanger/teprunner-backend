#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/12/24 14:50
@Desc    :  
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from teprunner.models import Project, Case, Task, TaskCase, TaskResult
from user.models import User


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
    creatorNickname = serializers.SerializerMethodField(required=False)
    projectId = serializers.CharField(source="project_id")

    class Meta:
        model = Case
        fields = ["id", "desc", "creatorNickname", "projectId", "filename", "filepath"]

    def get_creatorNickname(self, instance):
        creator_id = instance.creator_id
        user = User.objects.get(id=creator_id)
        return user.nickname


class TaskSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    projectId = serializers.CharField(source="project_id")
    taskStatus = serializers.CharField(source="task_status")
    taskCrontab = serializers.CharField(source="task_crontab", required=False, allow_blank=True)
    taskRunEnv = serializers.CharField(source="task_run_env", required=False, allow_blank=True)

    runEnv = serializers.SerializerMethodField(required=False)
    runUserNickname = serializers.SerializerMethodField(required=False)
    runTime = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Task
        fields = ["id", "name", "projectId", "taskStatus", "taskCrontab", "taskRunEnv",
                  "runEnv", "runUserNickname", "runTime"]

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
            run_user_id = task_results[0].run_user_id
            run_user_nickname = User.objects.get(id=run_user_id).nickname
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
        creator_id = Case.objects.get(id=case_id).creator_id
        return User.objects.get(id=creator_id).nickname


class TaskResultSerializer(serializers.ModelSerializer):
    taskId = serializers.CharField(source="task_id")
    caseDesc = serializers.SerializerMethodField(required=False)
    caseCreatorNickname = serializers.SerializerMethodField(required=False)
    runEnv = serializers.CharField(source="run_env")
    runUserNickname = serializers.SerializerMethodField()
    runTime = serializers.SerializerMethodField()
    reportPath = serializers.CharField(source="report_path")

    class Meta:
        model = TaskResult
        fields = ["taskId", "caseDesc", "caseCreatorNickname",
                  "result", "runEnv", "runUserNickname", "runTime", "reportPath"]

    def get_caseDesc(self, instance):
        return Case.objects.get(id=instance.case_id).desc

    def get_caseCreatorNickname(self, instance):
        creator_id = Case.objects.get(id=instance.case_id).creator_id
        return User.objects.get(id=creator_id).nickname

    def get_runUserNickname(self, instance):
        run_user_id = instance.run_user_id
        return User.objects.get(id=run_user_id).nickname

    def get_runTime(self, instance):
        return TaskResult.objects.get(id=instance.id).run_time.strftime("%Y-%m-%d %H:%M:%S")
