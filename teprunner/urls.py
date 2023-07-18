#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/11/24 11:01
@Desc    :  
"""

from django.urls import path

from teprunner.views import project, run, task, mock, tep_scaffold

urlpatterns = [
    path(r"scaffold", tep_scaffold.startproject),  # 项目脚手架

    path(r"mock/searchSku", mock.search_sku),
    path(r"mock/addCart", mock.add_cart),
    path(r"mock/order", mock.order),
    path(r"mock/pay", mock.pay),

    # ------------------项目开始------------------
    path(r"projects", project.ProjectViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"projects/<int:pk>", project.ProjectViewSet.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy"
    })),
    path(r"projects/env", project.project_env),  # 项目环境下拉框选项
    path(r"projects/<int:pk>/gitSync", project.git_sync),
    # ------------------项目结束------------------

    # ------------------任务开始------------------
    path(r"tasks", task.TaskViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"tasks/<int:pk>", task.TaskViewSet.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy"
    })),
    path(r"cases", task.cases),
    path(r"tasks/<int:task_id>/cases", task.TaskCaseView.as_view({
        "get": "list",
        "post": "add",
    })),
    path(r"tasks/<int:task_id>/cases/<int:case_id>", task.TaskCaseView.as_view({
        "delete": "remove"
    })),
    path(r"tasks/<int:task_id>/run", run.run_task),
    path(r"tasks/<int:task_id>/result", task.result),
    path(r"tasks/<int:task_id>/cases/<int:case_id>/result", task.case_result),
    path(r"tasks/<int:task_id>/report", task.report),
    # ------------------任务结束------------------
]
