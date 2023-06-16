#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2022/11/11 23:23
@Desc    :  
"""
import os

import yaml


class Config:
    project_root_dir = ""


def tep_config():
    """
    tep配置
    :return:
    """
    config_path = os.path.join(Config.project_root_dir, "resources", "tep.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)


def fixture_paths():
    """
    fixture路径，1、项目下的fixtures；2、tep下的fixture；
    :return:
    """
    _fixtures_dir = os.path.join(Config.project_root_dir, "fixtures")
    paths = []
    # 项目下的fixtures
    for root, _, files in os.walk(_fixtures_dir):
        for file in files:
            if file.startswith("fixture_") and file.endswith(".py"):
                full_path = os.path.join(root, file)
                import_path = full_path.replace(_fixtures_dir, "").replace("\\", ".")
                import_path = import_path.replace("/", ".").replace(".py", "")
                paths.append("fixtures" + import_path)
    # tep下的fixture
    paths.append("tep.fixture")
    return paths
