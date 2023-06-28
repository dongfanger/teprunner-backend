#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  dongfanger
@Date    :  7/23/2020 8:12 PM
@Desc    :  项目脚手架
"""

import os
import shutil

from django.http import StreamingHttpResponse
from loguru import logger
from rest_framework.decorators import api_view

from teprunner.views.project import file_iterator, make_zip
from teprunnerbackend import settings


def create_scaffold(project_name):
    """ 创建项目脚手架"""
    if os.path.isdir(project_name):
        logger.warning(
            f"Project folder {project_name} exists, please specify a new project name."
        )
        return 1
    elif os.path.isfile(project_name):
        logger.warning(
            f"Project name {project_name} conflicts with existed file, please specify a new one."
        )
        return 1

    print(f"Create new project: {project_name}")
    print(f"Project root dir: {os.path.join(os.getcwd(), project_name)}\n")

    def create_folder(path):
        os.makedirs(path)
        msg = f"Created folder: {path}"
        print(msg)

    def create_file(path, file_content=""):
        with open(path, "w", encoding="utf-8") as f:
            f.write(file_content)
        msg = f"Created file:   {path}"
        print(msg)

    create_folder(project_name)
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template")
    for root, dirs, files in os.walk(template_path):
        relative_path = root.replace(template_path, "").lstrip("\\").lstrip("/")
        if dirs:
            print(relative_path)
            for dir_ in dirs:
                create_folder(os.path.join(project_name, relative_path, dir_))
        if files:
            for file in files:
                with open(os.path.join(root, file), encoding="utf-8") as f:
                    create_file(os.path.join(project_name, relative_path, file[:file.find(".tep")]), f.read())


def copy_folder(source_folder, destination_folder, ignore_folders):
    shutil.copytree(source_folder, destination_folder, ignore=shutil.ignore_patterns(*ignore_folders))


@api_view(['POST'])
def create(request, *args, **kwargs):
    tep_dir = os.path.join(settings.BASE_DIR, "tep")
    temp_dir = os.path.join(settings.BASE_DIR, "export", "new_project")
    copy_folder(tep_dir, temp_dir, [".idea", ".pytest_cache", "venv", "__pycache__"])
    zip_filepath = os.path.join(settings.BASE_DIR, "export", "new_project.zip")
    make_zip(temp_dir, zip_filepath)
    shutil.rmtree(temp_dir)

    response = StreamingHttpResponse(file_iterator(zip_filepath))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment;filename={os.path.split(zip_filepath)[-1]}'

    return response
