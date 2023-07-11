#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/11/24 11:01
@Desc    :  
"""

from django.urls import path

from teprunner.views import project, envvar, fixture, case, run, plan, mock, tep_scaffold

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

    # ------------------用例开始------------------
    path(r"cases", case.CaseViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"cases/<int:pk>", case.CaseViewSet.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy"
    })),
    path(r"cases/<int:pk>/copy", case.copy_case),  # 复制用例
    path(r"cases/<int:pk>/run", run.run_case),  # 运行用例
    # ------------------用例结束------------------

    # ------------------任务开始------------------
    path(r"plans", plan.PlanViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"plans/<int:pk>", plan.PlanViewSet.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy"
    })),
    path(r"plans/<int:plan_id>/cases", plan.PlanCaseView.as_view({
        "get": "list",
        "post": "add",
    })),
    path(r"plans/<int:plan_id>/cases/<int:case_id>", plan.PlanCaseView.as_view({
        "delete": "remove"
    })),
    path(r"plans/<int:plan_id>/run", run.run_plan),
    path(r"plans/<int:plan_id>/result", plan.result),
    path(r"plans/<int:plan_id>/cases/<int:case_id>/result", plan.case_result),
    # ------------------任务结束------------------
]
