#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/12/24 14:50
@Desc    :  
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from teprunner.models import Project, EnvVar, Fixture, Case, CaseResult


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    envConfig = serializers.CharField(source="env_config")

    class Meta:
        model = Project
        fields = ["id", "name", "envConfig"]


class EnvVarSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    curProjectId = serializers.CharField(source="project_id")
    curEnvName = serializers.CharField(source="env_name")

    class Meta:
        model = EnvVar
        fields = ["id", "name", "value", "desc", "curProjectId", "curEnvName"]


class FixtureSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    creatorNickname = serializers.CharField(source="creator_nickname")
    curProjectId = serializers.CharField(source="project_id")

    class Meta:
        model = Fixture
        fields = ["id", "name", "desc", "code", "creatorNickname", "curProjectId"]


class CaseSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    creatorNickname = serializers.CharField(source="creator_nickname")
    projectId = serializers.CharField(source="project_id")

    class Meta:
        model = Case
        fields = ["id", "desc", "code", "creatorNickname", "projectId"]


class CaseListSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    creatorNickname = serializers.CharField(source="creator_nickname")
    projectId = serializers.CharField(source="project_id")

    result = serializers.SerializerMethodField(required=False)
    elapsed = serializers.SerializerMethodField(required=False)
    runEnv = serializers.SerializerMethodField(required=False)
    runUserNickname = serializers.SerializerMethodField(required=False)
    runTime = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Case
        fields = ["id", "desc", "code", "creatorNickname", "projectId",
                  "result", "elapsed", "runEnv", "runUserNickname", "runTime"]

    def get_result(self, instance):
        case_id = instance.id
        try:
            case_result = CaseResult.objects.filter(case_id=case_id).order_by('-run_time')
            if case_result:
                result = case_result[0].result
                return result
        except ObjectDoesNotExist:
            return ""
        return ""

    def get_elapsed(self, instance):
        case_id = instance.id
        try:
            case_result = CaseResult.objects.filter(case_id=case_id).order_by('-run_time')
            if case_result:
                elapsed = case_result[0].elapsed
                return elapsed
        except ObjectDoesNotExist:
            return ""
        return ""

    def get_runEnv(self, instance):
        case_id = instance.id
        try:
            case_result = CaseResult.objects.filter(case_id=case_id).order_by('-run_time')
            if case_result:
                run_env = case_result[0].run_env
                return run_env
        except ObjectDoesNotExist:
            return ""
        return ""

    def get_runUserNickname(self, instance):
        case_id = instance.id
        try:
            case_result = CaseResult.objects.filter(case_id=case_id).order_by('-run_time')
            if case_result:
                run_user_nickname = case_result[0].run_user_nickname
                return run_user_nickname
        except ObjectDoesNotExist:
            return ""
        return ""

    def get_runTime(self, instance):
        case_id = instance.id
        try:
            case_result = CaseResult.objects.filter(case_id=case_id).order_by('-run_time')
            if case_result:
                run_time = case_result[0].run_time
                return run_time.strftime("%Y-%m-%d %H:%M:%S")
        except ObjectDoesNotExist:
            return ""
        return ""


class CaseResultSerializer(serializers.ModelSerializer):
    caseId = serializers.IntegerField(source="case_id")
    runEnv = serializers.CharField(source="run_env")
    runUserNickname = serializers.CharField(source="run_user_nickname")
    runTime = serializers.SerializerMethodField(required=False)

    class Meta:
        model = CaseResult
        fields = ["caseId", "result", "elapsed", "output", "runEnv", "runUserNickname", "runTime"]

    def get_runTime(self, instance):
        return instance.run_time.strftime("%Y-%m-%d %H:%M:%S")
