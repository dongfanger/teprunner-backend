#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  dongfanger
@Date    :  8/14/2020 9:16 AM
@Desc    :  插件
"""
import json
import os
import shutil
import time

import allure_commons
import pytest
import yaml
from allure_commons.logger import AllureFileLogger
from allure_pytest.listener import AllureListener
from allure_pytest.plugin import cleanup_factory
from filelock import FileLock
from loguru import logger


class Config:
    project_root_dir = os.path.dirname(os.path.abspath(__file__))


def tep_config():
    """
    tep配置
    :return:
    """
    config_path = os.path.join(Config.project_root_dir, "resources", "tep.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)


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


# allure源文件临时目录，那一堆json文件，生成HTML报告会删除
allure_source_path = ".allure.source.temp"


def _tep_reports(config):
    """
    --tep-reports命令行参数不能和allure命令行参数同时使用，否则可能出错
    """
    if config.getoption("--tep-reports") and not config.getoption("allure_report_dir"):
        return True
    return False


def _is_master(config):
    """
    pytest-xdist分布式执行时，判断是主节点master还是子节点
    主节点没有workerinput属性
    """
    return not hasattr(config, 'workerinput')


reports_path = os.path.join(Config.project_root_dir, "reports")


def pytest_addoption(parser):
    """
    allure测试报告 命令行参数
    """
    parser.addoption(
        "--tep-reports",
        action="store_const",
        const=True,
        help="Create tep allure HTML reports."
    )


def pytest_configure(config):
    """
    这段代码源自：https://github.com/allure-framework/allure-python/blob/master/allure-pytest/src/plugin.py
    目的是生成allure源文件，用于生成HTML报告
    """
    if _tep_reports(config):
        if os.path.exists(allure_source_path):
            shutil.rmtree(allure_source_path)
        test_listener = AllureListener(config)
        config.pluginmanager.register(test_listener)
        allure_commons.plugin_manager.register(test_listener)
        config.add_cleanup(cleanup_factory(test_listener))

        clean = config.option.clean_alluredir
        file_logger = AllureFileLogger(allure_source_path, clean)  # allure_source
        allure_commons.plugin_manager.register(file_logger)
        config.add_cleanup(cleanup_factory(file_logger))


def pytest_sessionfinish(session):
    """
    测试运行结束后生成allure报告
    """
    reports_path = os.path.join(Config.project_root_dir, "reports")
    if _tep_reports(session.config):
        if _is_master(session.config):  # 只在master节点才生成报告
            # 最近一份报告的历史数据，填充allure趋势图
            if os.path.exists(reports_path):
                his_reports = os.listdir(reports_path)
                if his_reports:
                    latest_report_history = os.path.join(reports_path, his_reports[-1], "history")
                    shutil.copytree(latest_report_history, os.path.join(allure_source_path, "history"))

            current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
            html_report_name = os.path.join(reports_path, "report-" + current_time)
            os.system(f"allure generate {allure_source_path} -o {html_report_name}  --clean")
            shutil.rmtree(allure_source_path)


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
    return paths


pytest_plugins = fixture_paths()  # +[其他插件]
