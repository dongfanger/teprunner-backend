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
    git_repository = models.CharField("Git仓库", max_length=100, null=True, blank=True)
    git_branch = models.CharField("Git分支", max_length=100, null=True, blank=True)
    last_sync_time = models.DateTimeField("运行时间", null=True, blank=True)


class Case(BaseTable):
    class Meta:
        db_table = "case"

    desc = models.CharField("用例描述", max_length=500, null=False)
    creator_nickname = models.CharField("创建人昵称", null=False, max_length=64)
    project_id = models.IntegerField("项目id", null=False)
    filename = models.CharField("文件名", max_length=200, null=False, default="")
    filepath = models.CharField("文件路径", max_length=500, null=False, default="")


class Task(models.Model):
    class Meta:
        db_table = "task"

    name = models.CharField("测试计划名称", max_length=50, null=False)
    project_id = models.IntegerField("项目id", null=False)
    task_status = models.CharField("定时任务开关状态", max_length=1, null=True, blank=True, default="0")
    task_crontab = models.CharField("定时任务crontab表达式", max_length=20, null=True, blank=True, default="")
    task_run_env = models.CharField("定时任务运行环境", max_length=20, null=True, blank=True, default="")


class TaskCase(models.Model):
    class Meta:
        db_table = "task_case"

    task_id = models.IntegerField("任务id", null=False)
    case_id = models.IntegerField("用例id", null=False)


class TaskResult(models.Model):
    class Meta:
        db_table = "task_result"

    task_id = models.IntegerField("任务id", null=False)
    case_id = models.IntegerField("用例id", null=False)
    result = models.CharField("运行结果", max_length=50, null=False)
    elapsed = models.CharField("耗时", max_length=50, null=False)
    output = models.TextField("输出日志", null=False, default="")
    run_env = models.CharField("运行环境", max_length=20, null=False)
    run_user_nickname = models.CharField("运行用户昵称", null=False, max_length=64)
    run_time = models.DateTimeField("运行时间", auto_now=True)
