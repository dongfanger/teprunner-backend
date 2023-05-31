#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/12/24 16:29
@Desc    :  
"""
from rest_framework import status
from rest_framework.views import exception_handler
from teprunnerbackend.settings import MENU_AUTH

from user.models import Role, UserRole
from user.serializers import UserLoginSerializer


def jwt_response_payload_handler(token, user=None, request=None):
    # 自定义响应体
    role_id = UserRole.objects.get(user_id=user.id).role_id  # 获取角色id
    return {
        "token": token,
        "user": UserLoginSerializer(user).data,
        "auth": MENU_AUTH[Role.objects.get(id=role_id).name]  # 根据角色获取菜单
    }


def custom_exception_handler(exc, context):
    # 根据异常自定义响应体和状态码
    if hasattr(exc, "detail"):
        if exc.detail == "缺失JWT请求头":
            response = exception_handler(exc, context)
            response.data = {
                "msg": "缺失JWT请求头",
                "data": {}
            }
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return response
        if exc.detail == "Signature has expired.":
            response = exception_handler(exc, context)
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return response
    return exception_handler(exc, context)
