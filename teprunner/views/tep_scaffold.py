#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  dongfanger
@Date    :  7/23/2020 8:12 PM
@Desc    :  项目脚手架
"""

import os
import shutil
import zipfile

from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view

from teprunnerbackend import settings


def make_zip(source_dir, zip_filename):
    zip_ = zipfile.ZipFile(zip_filename, 'w')
    pre_len = len(os.path.dirname(source_dir))
    for parent, _, filenames in os.walk(source_dir):
        for filename in filenames:
            path = os.path.join(parent, filename)
            arcname = path[pre_len:].strip(os.path.sep)
            zip_.write(path, arcname)
    zip_.close()


def file_iterator(file_path, chunk_size=512):
    with open(file_path, mode='rb') as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


def copy_folder(source_folder, destination_folder, ignore_folders):
    shutil.copytree(source_folder, destination_folder, ignore=shutil.ignore_patterns(*ignore_folders))


def create_scaffold(project_dir):
    tep_dir = os.path.join(settings.SANDBOX_PATH, "tep-project")
    copy_folder(tep_dir, project_dir, ignore_folders=[".idea", ".pytest_cache", "venv", "__pycache__", ".git"])


@api_view(['POST'])
def startproject(request, *args, **kwargs):
    export_dir = os.path.join(settings.BASE_DIR, "export")
    temp_dir = os.path.join(export_dir, "newProject")
    create_scaffold(temp_dir)
    zip_filepath = os.path.join(export_dir, "newProject.zip")
    make_zip(temp_dir, zip_filepath)
    shutil.rmtree(temp_dir)

    response = StreamingHttpResponse(file_iterator(zip_filepath))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment;filename={os.path.split(zip_filepath)[-1]}'

    return response
