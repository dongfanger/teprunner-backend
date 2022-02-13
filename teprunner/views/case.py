#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2021/1/21 14:20
@Desc    :  
"""
import time

from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teprunner.models import Case, CaseResult, PlanCase
from teprunner.serializers import CaseSerializer, CaseResultSerializer, CaseListSerializer
from user.pagination import CustomPagination


class CaseViewSet(ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer

    def list(self, request, *args, **kwargs):
        project_id = request.GET.get("projectId")
        query = Q(project_id=project_id)  # Q查询条件
        case_id = request.GET.get("id")
        if case_id:  # 如果传了用例id
            query &= Q(id=case_id)
        desc = request.GET.get("desc")
        if desc:  # 如果传了用例描述
            query &= Q(desc__icontains=desc)
        api = request.GET.get("api")
        if api:  # 如果传了接口路径
            query &= Q(code__icontains=api)
        exclude_plan_id = request.GET.get("excludePlanId")
        if exclude_plan_id:  # 测试计划添加用例时，排除已经添加到当前计划的用例
            plan_case_ids = [plan_case.case_id for plan_case in PlanCase.objects.filter(plan_id=exclude_plan_id)]
            query &= ~Q(id__in=plan_case_ids)
        keyword = request.GET.get("keyword")
        if keyword:  # 如果传了关键字
            try:
                int(keyword)
                case_id_query = Q(id=keyword)  # 关键字既可以是用例id
            except ValueError:  # 对数字以外字符做异常处理
                case_id_query = Q()
            case_desc_query = Q(desc__icontains=keyword)  # 关键字也可以是用例描述
            query &= (case_id_query | case_desc_query)
        queryset = Case.objects.filter(query).order_by('-id')  # 按照用例id倒序
        cp = CustomPagination()
        page = cp.paginate_queryset(queryset, request=request)
        if page is not None:
            serializer = CaseListSerializer(page, many=True)
            return cp.get_paginated_response(serializer.data)

    def update(self, request, *args, **kwargs):
        case_id = kwargs["pk"]
        # 知道谁修改了用例
        request.data["creatorNickname"] = Case.objects.get(id=case_id).creator_nickname
        # ------------------复用代码--------------------
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    # ------------------复用代码--------------------


class CaseResultView(JsonWebsocketConsumer):
    # 继承channels.generic.websocket.JsonWebsocketConsumer
    # 可以接受和发送JSON的WebSocket消费者

    group_name = None
    case_id = None

    def connect(self):
        # 建立连接 从url中拿到case_id
        self.case_id = self.scope['url_route']['kwargs']['case_id']
        # 把case_id作为房间名
        self.group_name = str(self.case_id)
        # 在channel_layer中创建房间
        self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # 断开连接时，把房间从channel_layer中移除
        self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    def receive_json(self, content, **kwargs):
        # 在后端收到前端请求时调用 服务端会给客户端发4次消息
        case = Case.objects.get(id=self.case_id)
        res = {"desc": case.desc, "creatorNickname": case.creator_nickname,
               "result": "", "elapsed": "", "output": "",
               "runEnv": "", "runUserNickname": "", "runTime": ""}
        # 第1次，返回用例描述和用例创建人
        self.send_json(res)
        timeout = 60
        count = 1
        while count <= timeout:
            res["output"] = f"用例结果查询中{count}s"
            # 第2次，返回计时器
            self.send_json(res)
            try:
                instances = CaseResult.objects.filter(case_id=self.case_id).order_by('-run_time')
                serializer = CaseResultSerializer(instance=instances[0])
                res["result"] = serializer.data.get("result")
                res["elapsed"] = serializer.data.get("elapsed")
                res["output"] = serializer.data.get("output")
                res["runEnv"] = serializer.data.get("runEnv")
                res["runUserNickname"] = serializer.data.get("runUserNickname")
                res["runTime"] = serializer.data.get("runTime")
                # 第3次，返回用例结果
                self.send_json(res)
                break
            except (ObjectDoesNotExist, IndexError):
                count += 1
                time.sleep(1)
        if count > timeout:
            res["output"] = f"查询时间超过{timeout}s"
            # 第4次，60s后还没有结果，返回超时
            self.send_json(res)
        self.close()


@api_view(['POST'])
def copy_case(request, *args, **kwargs):
    case_id = kwargs["pk"]
    case = Case.objects.get(id=case_id)
    new_case = {
        "desc": case.desc + "--复制",
        "code": case.code,
        "creatorNickname": request.data.get("creatorNickname"),
        "projectId": case.project_id
    }
    serializer = CaseSerializer(data=new_case)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"msg": "用例复制成功"}, status=status.HTTP_200_OK)
