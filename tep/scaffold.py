#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  dongfanger
@Date    :  7/23/2020 8:12 PM
@Desc    :  项目脚手架
"""

import os
import platform
import sys

from loguru import logger


class ExtraArgument:
    """命令行附加参数映射"""
    # 是否创建Python虚拟环境
    create_venv = False


def init_parser_scaffold(subparsers):
    """定义参数"""
    sub_parser_scaffold = subparsers.add_parser("startproject", help="Create a new project with template structure.")
    sub_parser_scaffold.add_argument("project_name", type=str, nargs="?", help="Specify new project name.")
    sub_parser_scaffold.add_argument(
        "-venv",
        dest="create_venv",
        action="store_true",
        help="Create virtual environment in the project, and install tep.",
    )
    return sub_parser_scaffold


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
                    create_file(os.path.join(project_name, relative_path, file.rstrip(".tep")), f.read())

    if ExtraArgument.create_venv:
        # 创建Python虚拟环境
        os.chdir(project_name)
        print("\nCreating virtual environment")
        os.system("python -m venv .venv")
        print("Created virtual environment: .venv")

        # 在Python虚拟环境中安装tep
        print("Installing tep")
        if platform.system().lower() == 'windows':
            os.chdir(".venv")
            os.chdir("Scripts")
            os.system("pip install tep")
        elif platform.system().lower() == 'linux':
            os.chdir(".venv")
            os.chdir("bin")
            os.system("pip install tep")


def main_scaffold(args):
    # 项目脚手架处理程序入口
    ExtraArgument.create_venv = args.create_venv
    sys.exit(create_scaffold(args.project_name))


if __name__ == '__main__':
    create_scaffold("demo")
