from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from api.models import User, ProductInfo, Category, Product, Shop, ProductParameter, Parameter, Order, OrderItem, \
    Contact
import re


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
            raise ValidationError({"Status": False, "Errors": errors})

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
                raise ValidationError({"Status": False, 'Errors': 'Passwords do not match'})
            user.set_password(password)
            user.save()
        except KeyError:
            raise ValidationError({"Status": False, "Errors": 'Указаны не все параметры для регистрации пользователя'})

    def to_representation(self, instance):
        representation = {'Status': True}
        return representation

class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ['name']


class ParameterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Parameter
        fields = ['name']


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = ParameterSerializer(many=False)

    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value', ]


class ProductInfoSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(many=False)
    product_parameters = ProductParameterSerializer(many=True)

    class Meta:
        model = ProductInfo
        fields = ['price', 'price_rrc', 'shop', 'quantity', 'product_parameters', ]
        extra_kwargs = {
            'price_rrc': {'write_only': True},
        }


class ProductSerializer(serializers.ModelSerializer):
    products_info = ProductInfoSerializer(many=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'products_info']


class ProductListSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True)

    class Meta:
        model = Category
        fields = ['category', 'products']
        extra_kwargs = {
            'category': {'source': 'name', 'read_only': True}
        }


class ProductInfoSerializer2(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = ['id', 'price']
        read_only_fields = ['price', ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductInfoSerializer2

    class Meta:
        model = OrderItem
        fields = ['quantity', 'product', ]

    def validate(self, attrs):
        if attrs['product'].quantity < attrs['quantity']:
            raise ValidationError("Такого количества нет в наличии")
        elif attrs['quantity'] < 1:
            raise ValidationError("Нельзя заказать товар в количестве меньше 1 ед.")
        return attrs

    def create(self, validated_data):
        order = super().create(validated_data)
        order.save()
        return order


class ViewBasketSerializer(serializers.ModelSerializer):
    product = ProductInfoSerializer(many=False)

    class Meta:
        model = OrderItem
        fields = ['product_id', 'quantity', 'product']


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = ViewBasketSerializer(many=True, required=False)
    total_sum = serializers.IntegerField(required=False)

    class Meta:
        model = Order
        fields = ['id', 'dt', 'user_id', 'status', 'ordered_items', 'total_sum']


class ContactSerializer(serializers.ModelSerializer):
    @staticmethod
    def check_address(address):
        if {'город', 'улица', 'дом', 'квартира'} & set(address.split()):
            return True
        else:
            return False

    class Meta:
        model = Contact
        fields = ['type', 'user', 'value']

    def validate(self, attrs):
        if attrs['type'] == 'phone':
            if re.search(r"((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}", attrs['value']) is not None:
                return attrs
            else:
                raise ValidationError({'Status': False, 'Errors': "Некорректный формат номера"})
        elif attrs['type'] == 'address':
            if self.check_address(address=attrs['value']):
                return attrs
            else:
                raise ValidationError({'Status': False, 'Errors': "Некорректный формат адреса"})

    def to_representation(self, instance):
        rep = {"Status":True}
        return rep