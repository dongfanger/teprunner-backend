#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2022/11/20 20:34
@Desc    :  
"""
from loguru import logger


def test(env_vars):
    logger.info(env_vars["domain"])
    logger.info(env_vars["env"])
    logger.info(env_vars["db"]["mysql"]["host"])
