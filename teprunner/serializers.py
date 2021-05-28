#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/12/24 14:50
@Desc    :  
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from teprunner.models import Project, EnvVar, Fixture, Case, CaseResult, Plan, PlanCase, PlanResult


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


class PlanSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    projectId = serializers.CharField(source="project_id")
    taskStatus = serializers.CharField(source="task_status")
    taskCrontab = serializers.CharField(source="task_crontab")
    taskRunEnv = serializers.CharField(source="task_run_env")

    caseNum = serializers.SerializerMethodField(required=False)
    passedNum = serializers.SerializerMethodField(required=False)
    failedNum = serializers.SerializerMethodField(required=False)
    errorNum = serializers.SerializerMethodField(required=False)
    elapsed = serializers.SerializerMethodField(required=False)
    runEnv = serializers.SerializerMethodField(required=False)
    runUserNickname = serializers.SerializerMethodField(required=False)
    runTime = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Plan
        fields = ["id", "name", "projectId", "taskStatus", "taskCrontab", "taskRunEnv",
                  "caseNum", "passedNum", "failedNum", "errorNum", "elapsed", "runEnv", "runUserNickname", "runTime"]

    def get_caseNum(self, instance):
        plan_id = instance.id
        try:
            case_num = len(PlanCase.objects.filter(plan_id=plan_id))
        except ObjectDoesNotExist:
            return ""
        return str(case_num)

    def get_passedNum(self, instance):
        plan_id = instance.id
        try:
            passed_num = 0
            for plan_result in PlanResult.objects.filter(plan_id=plan_id):
                if ("passed" in plan_result.result
                        and "failed" not in plan_result.result
                        and "error" not in plan_result.result):
                    passed_num += 1
        except ObjectDoesNotExist:
            return ""
        return str(passed_num)

    def get_failedNum(self, instance):
        plan_id = instance.id
        try:
            failed_num = 0
            for plan_result in PlanResult.objects.filter(plan_id=plan_id):
                if "failed" in plan_result.result and "error" not in plan_result.result:
                    failed_num += 1
        except ObjectDoesNotExist:
            return ""
        return str(failed_num)

    def get_errorNum(self, instance):
        plan_id = instance.id
        try:
            error_num = 0
            for plan_result in PlanResult.objects.filter(plan_id=plan_id):
                if "error" in plan_result.result:
                    error_num += 1
        except ObjectDoesNotExist:
            return ""
        return str(error_num)

    def get_elapsed(self, instance):
        plan_id = instance.id
        try:
            total_elapsed = 0
            for plan_result in PlanResult.objects.filter(plan_id=plan_id):
                total_elapsed += float(plan_result.elapsed.replace("s", ""))
        except ObjectDoesNotExist:
            return ""
        return str(total_elapsed)[:4] + "s"

    def get_runEnv(self, instance):
        plan_id = instance.id
        try:
            plan_results = PlanResult.objects.filter(plan_id=plan_id)
        except ObjectDoesNotExist:
            return ""
        run_env = ""
        if plan_results:
            run_env = plan_results[0].run_env
        return run_env

    def get_runUserNickname(self, instance):
        plan_id = instance.id
        try:
            plan_results = PlanResult.objects.filter(plan_id=plan_id)
        except ObjectDoesNotExist:
            return ""
        run_user_nickname = ""
        if plan_results:
            run_user_nickname = plan_results[0].run_user_nickname
        return run_user_nickname

    def get_runTime(self, instance):
        plan_id = instance.id
        try:
            plan_results = PlanResult.objects.filter(plan_id=plan_id)
        except ObjectDoesNotExist:
            return ""
        run_time = ""
        if plan_results:
            run_time = plan_results.order_by('run_time')[0].run_time.strftime("%Y-%m-%d %H:%M:%S")
        return run_time


class PlanCaseSerializer(serializers.ModelSerializer):
    planId = serializers.CharField(source="plan_id")
    caseId = serializers.CharField(source="case_id")
    caseDesc = serializers.SerializerMethodField(required=False)
    caseCreatorNickname = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PlanCase

        fields = ["planId", "caseId", "caseDesc", "caseCreatorNickname"]

    def get_caseDesc(self, instance):
        plan_case_id = instance.id
        case_id = PlanCase.objects.get(id=plan_case_id).case_id
        return Case.objects.get(id=case_id).desc

    def get_caseCreatorNickname(self, instance):
        plan_case_id = instance.id
        case_id = PlanCase.objects.get(id=plan_case_id).case_id
        return Case.objects.get(id=case_id).creator_nickname


class PlanResultSerializer(serializers.ModelSerializer):
    planId = serializers.CharField(source="plan_id")
    caseId = serializers.CharField(source="case_id")
    caseDesc = serializers.SerializerMethodField(required=False)
    caseCreatorNickname = serializers.SerializerMethodField(required=False)
    runEnv = serializers.CharField(source="run_env")
    runUserNickname = serializers.CharField(source="run_user_nickname")
    runTime = serializers.SerializerMethodField()

    class Meta:
        model = PlanResult
        fields = ["planId", "caseId", "caseDesc", "caseCreatorNickname",
                  "result", "elapsed", "output", "runEnv", "runUserNickname", "runTime"]

    def get_caseDesc(self, instance):
        return Case.objects.get(id=instance.case_id).desc

    def get_caseCreatorNickname(self, instance):
        return Case.objects.get(id=instance.case_id).creator_nickname

    def get_runTime(self, instance):
        return PlanResult.objects.get(id=instance.id).run_time.strftime("%Y-%m-%d %H:%M:%S")

    def to_representation(self, obj):
        ret = super(PlanResultSerializer, self).to_representation(obj)
        ret.pop('output')
        return ret
