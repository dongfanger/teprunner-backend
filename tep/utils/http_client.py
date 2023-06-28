#!/usr/bin/python
# encoding=utf-8

import decimal
import json
import time

import allure
import jsonpath
import requests
import urllib3
from loguru import logger
from requests import Response

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def request(method, url, **kwargs):
    template = """\n
Request URL: {}
Request Method: {}
Request Headers: {}
Request Payload: {}
Status Code: {}
Response: {}
Elapsed: {}
"""
    start = time.process_time()
    response = requests.request(method, url, **kwargs)  # requests.request原生用法
    end = time.process_time()
    elapsed = str(decimal.Decimal("%.3f" % float(end - start))) + "s"
    headers = kwargs.get("headers", {})
    kwargs.pop("headers")
    payload = kwargs
    log = template.format(url, method, json.dumps(headers), json.dumps(payload), response.status_code, response.text,
                          elapsed)
    logger.info(log)
    allure.attach(log, f'request & response', allure.attachment_type.TEXT)
    return TepResponse(response)


class TepResponse(Response):
    """
    二次封装requests.Response，添加额外方法
    """

    def __init__(self, response):
        super().__init__()
        for k, v in response.__dict__.items():
            self.__dict__[k] = v

    def jsonpath(self, expr):
        """
        此处强制取第一个值，便于简单取值
        如果复杂取值，建议直接jsonpath原生用法
        """
        return jsonpath.jsonpath(self.json(), expr)[0]
