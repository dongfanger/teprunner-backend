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
