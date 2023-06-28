#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  dongfanger
@Date    :  5/16/2022 5:41 PM
@Desc    :  常用函数
"""
from utils import function


def test_time():
    """时间日期"""
    print(func.current_time())  # 2022-05-19 21:55:21
    print(func.current_date())  # 2022-05-19


def test_print():
    """打印文本"""
    for i in range(101):
        print(func.print_progress_bar(i))  # 99% [■■■■■■■■■□]


def test_case():
    """自动生成功能测试用例"""
    pl = [['M', 'O', 'P'], ['W', 'L', 'I'], ['C', 'E']]
    a = func.case_pairwise(pl)  # 笛卡尔积:18 过滤后:9
    print()
    for i in a:
        print(i)
