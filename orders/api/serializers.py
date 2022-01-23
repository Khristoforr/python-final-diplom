from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.models import User


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['id', 'last_name', 'first_name', 'email', 'password', 'password2', 'company', 'position', 'username']
        extra_kwargs = {"password": {"write_only": True}}


    def validate_password(self, value):
        errors = dict()
        try:
            validate_password(value)

        except ValidationError as password_error:
            errors['password'] = list(password_error.messages)

        if errors:
            raise ValidationError(errors)

        return super(UserSerializer, self).validate(value)

    def save(self):
        try:
            user = User(
                last_name=self.validated_data['last_name'],
                first_name=self.validated_data['first_name'],
                email=self.validated_data['email'],
                company=self.validated_data['company'],
                position=self.validated_data['position'],
                username=self.validated_data['username']
            )
            password = self.validated_data['password']
            password2 = self.validated_data['password2']
            if password != password2:
                raise ValidationError({'password': 'Passwords do not match'})
            user.password = password
            user.save()
        except KeyError:
            raise ValidationError('Указаны не все параметры для регистрации пользователя')


# class UploadSerializer(serializers.ModelSerializer):
#     filename = serializers.FileField(max_length=None, use_url=True)
#
#     class Meta:
#         model = Shop
#         fields = ['name', 'url', 'filename']
