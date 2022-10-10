import redis
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import CharField, Serializer, IntegerField
from rest_framework_simplejwt.serializers import PasswordField
from rest_framework_simplejwt.tokens import RefreshToken

from django_validation.custom_validations import PhoneNumberUserExistenceValidator
from django_validation.model_validations import ValueStartsWithValidator

from django.contrib.auth import get_user_model

User = get_user_model()


class UsernamePasswordLoginResponseSerializer(Serializer):
    refresh = CharField(read_only=True)
    access = CharField(read_only=True)


class CreateOtpPostSerializer(Serializer):
    otp_code = IntegerField(read_only=True)
    phone_number = CharField(max_length=11, min_length=11, required=True, allow_null=False, allow_blank=False, validators=[ValueStartsWithValidator(limit_value='0')])
    otp_code_length = IntegerField(default=5, allow_null=False, min_value=3)
    expire_time = IntegerField(default=120, allow_null=False, min_value=60, help_text='please enter expire time in second')
    role_name = CharField(allow_null=True, allow_blank=False, default=None, help_text='for searching in all users account, role_name value should be null')

    def validate_phone_number(self, value):
        PhoneNumberUserExistenceValidator(self.initial_data.get('role_name')).__call__(value)
        return value


class ValidateOtpPostSerializer(Serializer):
    phone_number = CharField(max_length=11, min_length=11, required=True, allow_null=False, allow_blank=False, validators=[ValueStartsWithValidator(limit_value='0')])
    otp_code = IntegerField(required=True, allow_null=False)
    token_class = RefreshToken

    def validate_phone_number(self, value):
        PhoneNumberUserExistenceValidator(self.initial_data.get('role_name')).__call__(value)
        return value

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)

    def validate(self, attrs):
        validated_data = super(ValidateOtpPostSerializer, self).validate(attrs)
        r = redis.StrictRedis()
        if bool(r.exists(validated_data.get('phone_number'))):
            if validated_data.get('otp_code') == int(r.get(validated_data.get('phone_number'))):
                return validated_data

        raise ValidationError(code='incorrect_otp_code', detail='Otp code is not correct')


class ResetPasswordPostSerializer(Serializer):
    password = PasswordField(required=True, allow_null=False, allow_blank=False)
    phone_number = CharField(max_length=11, min_length=11, required=True, allow_null=False, allow_blank=False, validators=[ValueStartsWithValidator(limit_value='0')])

    @staticmethod
    def change_password(validated_data):
        user = User.objects.filter(phone_number=validated_data.get('phone_number'), is_active=True).first()
        user.set_password(validated_data.get('password'))
        user.save()
        return validated_data
