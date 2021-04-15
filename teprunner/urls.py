#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/11/24 11:01
@Desc    :  
"""

from django.urls import path

from teprunner.views import project, envvar, fixture, case, run, plan

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

    path(r"cases", case.CaseViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"cases/<int:pk>", case.CaseViewSet.as_view({
        "get": "retrieve",
        "put": "update",
        "delete": "destroy"
    })),
    path(r"cases/<int:pk>/copy", case.copy_case),

    path(r"cases/<int:pk>/run", run.run_case),
    path(r"projects/<int:pk>/export", project.export_project),

    path(r"plans", plan.PlanViewSet.as_view({
        "get": "list",
        "post": "create"
    })),
    path(r"plans/<int:plan_id>", plan.PlanViewSet.as_view({
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
]
