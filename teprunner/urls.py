#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/11/24 11:01
@Desc    :  
"""

from django.urls import path

from teprunner.views import project, envvar, fixture

urlpatterns = [
    path(r"projects", project.ProjectViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"projects/<int:pk>", project.ProjectViewSet.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy"
    })),
    path(r"projects/env", project.project_env),

    path(r"envvars", envvar.EnvVarViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"envvars/<int:pk>", envvar.EnvVarViewSet.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy"
    })),

    path(r"fixtures", fixture.FixtureViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"fixtures/<int:pk>", fixture.FixtureViewSet.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy"
    })),
]
