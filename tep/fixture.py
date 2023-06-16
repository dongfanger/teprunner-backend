#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  dongfanger
@Date    :  2020/12/30 9:30
@Desc    :  预置fixture
"""
import json
import os

import pytest
import yaml
from filelock import FileLock
from loguru import logger

from tep.config import tep_config, Config


@pytest.fixture(scope="session")
def global_vars():
    """
    全局变量，读取resources/global_vars.yaml，返回字典
    """
    return _load_yaml(os.path.join(Config.project_root_dir, "resources", "global_vars.yaml"))


@pytest.fixture(scope="session")
def env_vars():
    """
    环境变量，读取resources/env_vars下的变量模板，返回字典
    """
    env_active = tep_config()['env']["active"]
    env_filename = f"env_vars_{env_active}.yaml"
    return _load_yaml(os.path.join(Config.project_root_dir, "resources", "env_vars", env_filename))


@pytest.fixture(scope="session")
def case_vars():
    """
    测试用例的动态变量，1条测试用例1个实例，彼此隔离
    """

    class CaseVars:
        def __init__(self):
            self.dict_in_memory = {}

        def put(self, key, value):
            self.dict_in_memory[key] = value

        def get(self, key):
            value = ""
            try:
                value = self.dict_in_memory[key]
            except KeyError:
                logger.error(f"获取用例变量的key不存在，返回空串: {key}")
            return value

    return CaseVars()


@pytest.fixture(scope="session")
def tep_context_manager(tmp_path_factory, worker_id):
    """
    tep上下文管理器，在xdist分布式执行时，多个session也只执行一次
    参考：https://pytest-xdist.readthedocs.io/en/latest/how-to.html#making-session-scoped-fixtures-execute-only-once
    命令不带-n auto也能正常执行，不受影响
    """

    def inner(produce_expensive_data, *args, **kwargs):
        if worker_id == "master":
            # not executing in with multiple workers, just produce the data and let
            # pytest's fixture caching do its job
            return produce_expensive_data(*args, **kwargs)

        # get the temp directory shared by all workers
        root_tmp_dir = tmp_path_factory.getbasetemp().parent

        fn = root_tmp_dir / "data.json"
        with FileLock(str(fn) + ".lock"):
            if fn.is_file():
                data = json.loads(fn.read_text())
            else:
                data = produce_expensive_data(*args, **kwargs)
                fn.write_text(json.dumps(data))
        return data

    return inner


def _load_yaml(path: str) -> dict:
    """
    加载yaml文件
    :param path:
    :return:
    """
    with open(path, encoding="utf8") as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)
