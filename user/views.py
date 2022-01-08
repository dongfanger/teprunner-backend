# Create your views here.
from datetime import datetime

import jwt
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import JSONWebTokenAPIView, jwt_response_payload_handler

from user.errors import ErrInvalidOldPassword, ErrInvalidPassword, ErrUserNotFound, ErrInvalidUserID
from user.models import User, Role, UserRole
from user.serializers import UserPagingSerializer, RolePagingSerializer, UserCreateSerializer, UserRoleSerializer


class UserLogin(JSONWebTokenAPIView):
    # 固定写法
    serializer_class = JSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        try:
            # 数据库加密后的密码
            db_password_hash = User.objects.get(username=username).password
        except User.DoesNotExist:
            return Response(ErrUserNotFound, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # 验证明文密码跟加密后的密码是否匹配
        if not check_password(password, db_password_hash):
            return Response(ErrInvalidPassword, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ----------------- 复用代码开始 -----------------
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)
            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # ----------------- 复用代码结束 -----------------


class UserViewSet(GenericViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserPagingSerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        keyword = request.GET.get("keyword")
        if keyword:
            queryset = User.objects.filter(Q(username__icontains=keyword) | Q(nickname__icontains=keyword))

        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        password = request.data.get("password")
        user = {
            "username": request.data.get("username"),
            "nickname": request.data.get("nickname"),
            "password": make_password(password) if password else make_password("qa123456")
        }
        role_names = request.data.get("roleNames")
        if "管理员" in role_names:
            user["is_staff"] = True
        else:
            user["is_staff"] = False
        user_create_serializer = UserCreateSerializer(data=user)
        user_create_serializer.is_valid(raise_exception=True)
        user_create_serializer.save()
        user_id = User.objects.get(username=user["username"]).id

        user_role = {
            "user_id": user_id,
            "role_id": ""
        }
        for role_name in role_names:
            role_id = Role.objects.get(name=role_name).id
            user_role["role_id"] = role_id
            user_role_serializer = UserRoleSerializer(data=user_role)
            user_role_serializer.is_valid(raise_exception=True)
            user_role_serializer.save()

        return Response(user_create_serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        user = {
            "id": kwargs["pk"],
            "username": request.data.get("username"),
            "nickname": request.data.get("nickname"),
        }
        role_names = request.data.get("roleNames")
        if "管理员" in role_names:
            user["is_staff"] = True
        else:
            user["is_staff"] = False
        instance = self.get_object()
        user_serializer = self.get_serializer(instance, data=user)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        user_id = User.objects.get(username=user["username"]).id

        user_role = {
            "user_id": user_id,
            "role_id": ""
        }
        db_role_ids = [obj.role_id for obj in UserRole.objects.filter(user_id=user_id)]
        db_role_names = [Role.objects.get(id=db_role_id).name for db_role_id in db_role_ids]

        new_roles = list(set(role_names).difference(db_role_names))
        old_roles = list(set(db_role_names).difference(role_names))
        for new_role in new_roles:
            role_id = Role.objects.get(name=new_role).id
            user_role["role_id"] = role_id
            user_role_serializer = UserRoleSerializer(data=user_role)
            user_role_serializer.is_valid(raise_exception=True)
            user_role_serializer.save()
        for old_role in old_roles:
            role_id = Role.objects.get(name=old_role).id
            user_role = UserRole.objects.get(user_id=user_id, role_id=role_id)
            user_role.delete()

        return Response(user_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        try:
            user_id = kwargs["pk"]
            user = User.objects.get(id=user_id)
            user.delete()
            user_roles = UserRole.objects.filter(user_id=user_id)
            for user_role in user_roles:
                user_role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response(ErrUserNotFound, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def user_detail(self, request, *args, **kwargs):
        try:
            user_id = kwargs["pk"]
            user = User.objects.get(id=user_id)
            user_serializer = self.get_serializer(user)
            return Response(user_serializer.data)
        except ObjectDoesNotExist:
            return Response(ErrUserNotFound, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RoleList(ListAPIView):
    queryset = Role.objects.all().order_by("id")
    serializer_class = RolePagingSerializer
    permission_classes = [IsAdminUser]


class SystemResetPassword(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, *args, **kwargs):
        user_id = kwargs["pk"]
        try:
            user = User.objects.get(id=user_id)
        except:
            return Response(ErrInvalidUserID, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        user.set_password("qa123456")
        user.save()
        return Response("qa123456")


@api_view(['PUT'])
def update_password(request, *args, **kwargs):
    request_jwt = request.headers.get("Authorization").replace("Bearer ", "")
    request_jwt_decoded = jwt.decode(request_jwt, verify=False, algorithms=['HS512'])
    user_id = request_jwt_decoded["user_id"]
    user = User.objects.get(id=user_id)
    db_password_hash = user.password
    old_password = request.data.get("oldPassword")
    new_password = request.data.get("newPassword")
    if not check_password(old_password, db_password_hash):
        return Response(ErrInvalidOldPassword, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    user.set_password(new_password)
    user.save()
    return Response(status=status.HTTP_200_OK)
