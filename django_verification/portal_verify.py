import functools
import random
import string

import redis
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .portal_verify_serializer import UsernamePasswordLoginResponseSerializer, CreateOtpPostSerializer, ValidateOtpPostSerializer, \
    ResetPasswordPostSerializer
from .portal_verify_swagger import get_verify_swagger_kwargs
from django.contrib.auth import get_user_model

User = get_user_model()


def add_role_to_query(role_name=None):
    def wrapper(func):
        @functools.wraps(func)
        def cash_reload(*args, **kwargs):
            request = args[0].request
            request.GET.update({'role': role_name})
            return func(*args, **kwargs)

        return cash_reload

    return wrapper


class PortalVerificationView(GenericViewSet):
    permission_classes = [AllowAny]

    serializers_dict = dict(
        POST=dict(
            login={'request_body': TokenObtainPairSerializer, 'responses': {200: UsernamePasswordLoginResponseSerializer}},
            create_otp_code={'request_body': CreateOtpPostSerializer},
            validate_otp_code={'request_body': ValidateOtpPostSerializer, 'responses': {200: UsernamePasswordLoginResponseSerializer}},
            reset_password={'request_body': ResetPasswordPostSerializer},
        ),
        GET=dict()
    )

    def get_serializer_class(self):
        return self.serializers_dict.get(self.request.method).get(self.action).get('request_body')

    @swagger_auto_schema(**get_verify_swagger_kwargs(method='POST', action_name='login', serializer=serializers_dict.get('POST')))
    @action(methods=['POST'], detail=False)
    def login(self, request):
        """
        login by username and password
        @return: token and refresh token
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(**get_verify_swagger_kwargs(method='POST', action_name='create_otp_code', serializer=serializers_dict.get('POST')))
    @action(methods=['POST'], detail=False, url_path='otp_code/create')
    def create_otp_code(self, request):
        """
        create otp code with given length and expire time in request data using redis
        @return: otp code
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        code = ''.join(random.choices(string.digits, k=data.get('otp_code_length')))
        r = redis.StrictRedis()
        r.set(data.get('phone_number'), code)
        r.expire(data.get('phone_number'), data.get('expire_time'))
        data.update({'otp_code': code})
        return Response(data)

    @swagger_auto_schema(**get_verify_swagger_kwargs(method='POST', action_name='validate_otp_code', serializer=serializers_dict.get('POST')))
    @action(methods=['POST'], detail=False, url_path='otp_code/validate')
    def validate_otp_code(self, request):
        """
        validate otp code with given phone_number
        @return: token and refresh token
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validate_data = serializer.validated_data
        refresh = serializer.get_token(User.objects.get(phone_number=validate_data.get('phone_number')))
        data = {'refresh': str(refresh), 'access': str(refresh.access_token)}
        return Response(data)

    @swagger_auto_schema(**get_verify_swagger_kwargs(method='POST', action_name='reset_password', serializer=serializers_dict.get('POST')))
    @action(methods=['POST'], detail=False, permission_classes=[IsAuthenticated])
    def reset_password(self, request):
        """
        reset user password with phone_number and new password
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.change_password(serializer.validated_data)
        return Response(data)

    # @swagger_auto_schema(**get_verify_swagger_kwargs(method='POST', action_name='authorize', serializer=serializers_dict.get('POST')))
    # @add_role_to_query()
    # @action(methods=['POST'], detail=False)
    # def authorize_role(self, request):
    #     if has_role(request.user, request.GET.get('role')):
    #         return self.authorize(request)
    #     raise ValidationError(code='user_role_denied', detail={'user does not have required role'})
