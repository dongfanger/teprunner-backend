#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/11/24 11:01
@Desc    :  
"""

from django.urls import path

from user import views

urlpatterns = [
    path(r"login", views.UserLogin.as_view()),

    path(r"", views.UserViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"<int:pk>", views.UserViewSet.as_view({
        "get": "user_detail",
        "put": "put",
        "delete": "delete"
    })),

    path(r"<int:pk>/passwords/reset", views.SystemResetPassword.as_view()),

    path(r"roles", views.RoleList.as_view()),

    path(r"passwords/set", views.update_password),
]
