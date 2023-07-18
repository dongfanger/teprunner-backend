#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/12/24 14:50
@Desc    :  
"""

from rest_framework import serializers

from user.models import User, Role, UserRole


class UserLoginSerializer(serializers.ModelSerializer):
    # 定义登录的返回字段
    # 固定写法，表示是通过自定义方法取值
    roleName = serializers.SerializerMethodField()

    class Meta:
        model = User
        # 从表中直接取值
        fields = ['username', 'nickname', 'roleName']

    def get_roleName(self, instance):
        # instance就是class Meta里面指定的model
        user_id = instance.id
        role_ids = [obj.role_id for obj in UserRole.objects.filter(user_id=user_id)]
        query_set = [Role.objects.get(id=role_id) for role_id in role_ids]
        return "、".join([obj.name for obj in query_set])


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'nickname', 'password', "is_staff"]


class UserPagingSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    roleNames = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'roleNames', "is_staff"]

    def get_roleNames(self, instance):
        user_id = instance.id
        role_ids = [obj.role_id for obj in UserRole.objects.filter(user_id=user_id)]
        query_set = [Role.objects.get(id=role_id) for role_id in role_ids]
        return [{"id": obj.id, "name": obj.name} for obj in query_set]


class RoleAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['auth']


class RolePagingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name"]


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['user_id', 'role_id']
