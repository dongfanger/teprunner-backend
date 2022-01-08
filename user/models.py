from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.


class BaseTable(models.Model):
    # 基础表 统一添加创建时间和更新时间字段
    class Meta:
        abstract = True  # 不会创建表
        db_table = 'BaseTable'

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)


class User(AbstractUser):
    # 用户表
    class Meta:
        db_table = "user"

    REQUIRED_FIELDS = []  # 让Django默认必填的邮箱变成非必填
    nickname = models.CharField("昵称", null=False, max_length=64, default="")


class Role(BaseTable):
    # 角色表
    class Meta:
        db_table = "role"

    name = models.CharField("角色名", null=False, max_length=64, default="")
    auth = models.JSONField("菜单权限JSON", default=None)


class UserRole(BaseTable):
    # 用户角色关系表
    class Meta:
        db_table = "user_role"

    user_id = models.IntegerField("用户id", null=False, default=0)
    role_id = models.IntegerField("角色id", null=False, default=0)
