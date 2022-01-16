#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/12/25 17:29
@Desc    :  
"""

from collections import OrderedDict

from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    # 自定义分页器 主要是重命名+添加字段
    page_query_param = "page"
    page_size_query_param = "perPage"

    def get_paginated_response(self, data):
        current_page = self.page.number
        total_num = self.page.paginator.count
        total_page = self.page.paginator.num_pages
        return Response(OrderedDict([
            ('currentPage', current_page),
            ('hasNext', True if self.get_next_link() else False),
            ('hasPrev', True if self.get_previous_link() else False),
            ('items', data),
            ('totalNum', total_num),
            ('totalPage', total_page),
        ]))
