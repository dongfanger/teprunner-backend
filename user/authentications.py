#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Don
@Date    :  2020/11/24 15:48
@Desc    :  
"""
import jwt
from rest_framework import exceptions
from rest_framework_jwt.authentication import BaseJSONWebTokenAuthentication, JSONWebTokenAuthentication
from rest_framework_jwt.authentication import get_authorization_header
from rest_framework_jwt.authentication import jwt_decode_handler

from user.models import User


class CustomJSONWebTokenAuthentication(BaseJSONWebTokenAuthentication):
    def authenticate(self, request):
        authorization_header = get_authorization_header(request)
        if not authorization_header:
            raise exceptions.AuthenticationFailed('缺失JWT请求头')

        jwt_value = JSONWebTokenAuthentication().get_jwt_value(request)
        if jwt_value is None:
            return None

        try:
            payload = jwt_decode_handler(jwt_value)
        except jwt.ExpiredSignature:
            raise exceptions.AuthenticationFailed('Signature has expired.')
        except (jwt.DecodeError, User.DoesNotExist):
            raise exceptions.AuthenticationFailed('Error decoding signature.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed()

        user = self.authenticate_credentials(payload)
        return user, jwt_value
