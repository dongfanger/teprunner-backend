from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.


class BaseTable(models.Model):
    class Meta:
        abstract = True
        db_table = 'BaseTable'

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)


class User(AbstractUser):
    class Meta:
        db_table = "user"

    REQUIRED_FIELDS = []
    nickname = models.CharField("昵称", null=False, max_length=64, default="")


class Role(BaseTable):
    class Meta:
        db_table = "role"

    name = models.CharField("角色名", null=False, max_length=64, default="")
    auth = models.JSONField("菜单权限JSON", default=None)


class UserRole(BaseTable):
    class Meta:
        db_table = "user_role"

    user_id = models.IntegerField("用户id", null=False, default=0)
    role_id = models.IntegerField("角色id", null=False, default=0)
