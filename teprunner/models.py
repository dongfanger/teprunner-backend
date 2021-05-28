from django.db import models


# Create your models here.
class BaseTable(models.Model):
    class Meta:
        abstract = True
        db_table = 'BaseTable'

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)


class Project(BaseTable):
    class Meta:
        db_table = "project"

    name = models.CharField("项目名称", unique=True, max_length=100, null=False)
    env_config = models.CharField("环境配置", max_length=100, null=False)


class EnvVar(BaseTable):
    class Meta:
        db_table = "env_var"
        unique_together = (("project_id", "env_name", "name"),)

    name = models.CharField("变量名", max_length=50, null=False)
    value = models.CharField("变量值", max_length=100, null=False)
    desc = models.CharField("描述", max_length=200, default="")
    project_id = models.IntegerField("项目id", null=False)
    env_name = models.CharField("环境名称", max_length=20, null=False)


class Fixture(BaseTable):
    class Meta:
        db_table = "fixture"

    name = models.CharField("fixture名称", max_length=100, null=False)
    desc = models.CharField("fixture描述", max_length=500, default="")
    code = models.TextField("代码", max_length=30000, null=False)
    creator_nickname = models.CharField("创建人昵称", null=False, max_length=64)
    project_id = models.IntegerField("项目id", null=False)


class Case(BaseTable):
    class Meta:
        db_table = "case"

    desc = models.CharField("用例描述", max_length=500, null=False)
    code = models.TextField("代码", max_length=30000, null=False)
    creator_nickname = models.CharField("创建人昵称", null=False, max_length=64)
    project_id = models.IntegerField("项目id", null=False)


class CaseResult(BaseTable):
    class Meta:
        db_table = "case_result"

    case_id = models.IntegerField("用例id", null=False)
    result = models.CharField("运行结果", max_length=50, null=False)
    elapsed = models.CharField("耗时", max_length=50, null=False)
    output = models.TextField("输出日志", null=False, default="")
    run_env = models.CharField("运行环境", max_length=20, null=False)
    run_user_nickname = models.CharField("运行用户昵称", null=False, max_length=64)
    run_time = models.DateTimeField("运行时间", auto_now=True)


class Plan(models.Model):
    class Meta:
        db_table = "plan"

    name = models.CharField("测试计划名称", max_length=50, null=False)
    project_id = models.IntegerField("项目id", null=False)
    task_status = models.CharField("定时任务开关状态", max_length=1, null=True, blank=True, default="0")
    task_crontab = models.CharField("定时任务crontab表达式", max_length=20, null=True, blank=True, default="")
    task_run_env = models.CharField("定时任务运行环境", max_length=20, null=False, default="")


class PlanCase(models.Model):
    class Meta:
        db_table = "plan_case"

    plan_id = models.IntegerField("测试计划id", null=False)
    case_id = models.IntegerField("用例id", null=False)


class PlanResult(models.Model):
    class Meta:
        db_table = "plan_result"

    plan_id = models.IntegerField("计划id", null=False)
    case_id = models.IntegerField("用例id", null=False)
    result = models.CharField("运行结果", max_length=50, null=False)
    elapsed = models.CharField("耗时", max_length=50, null=False)
    output = models.TextField("输出日志", null=False, default="")
    run_env = models.CharField("运行环境", max_length=20, null=False)
    run_user_nickname = models.CharField("运行用户昵称", null=False, max_length=64)
    run_time = models.DateTimeField("运行时间", auto_now=True)
