from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.models import User, ProductInfo, Category, Product, Shop


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['id', 'last_name', 'first_name', 'email', 'password',
                  'password2', 'company', 'position', 'username', 'type']
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
                username=self.validated_data['username'],
                type=self.validated_data['type']
            )
            password = self.validated_data['password']
            password2 = self.validated_data['password2']
            if password != password2:
                raise ValidationError({'password': 'Passwords do not match'})
            user.set_password(password)
            user.save()
        except KeyError:
            raise ValidationError('Указаны не все параметры для регистрации пользователя')


class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ['name']


class ProductInfoSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(many=False)

    class Meta:
        model = ProductInfo
        fields = ['price', 'price_rrc', 'shop']


class ProductSerializer(serializers.ModelSerializer):
    products_info = ProductInfoSerializer(many=True)

    class Meta:
        model = Product
        fields = ['name', 'products_info']


class ProductListSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    class Meta:
        model = Category
        fields = ['category', 'products']
        extra_kwargs = {
            'category': {'source': 'name', 'read_only': True}
        }
