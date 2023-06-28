#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2022/11/20 18:40
@Desc    :  
"""

from faker import Faker


def test():
    print(Faker().name())
    print(Faker(locale="zh_CN").name())
    print(Faker(locale="en").name())
