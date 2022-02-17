import json

import pytest
from model_bakery import baker
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from api.models import User


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_token(client):
    user = User.objects.create_user(email='123@mail.ru', username='evgenii', password='rnhsdf2', is_active=True)
    token = Token.objects.create(user=user)
    return client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')


@pytest.fixture
def user_info():
    return {'first_name': 'Evgenii',
            'last_name': 'Khristoforov',
            'email': 'khristoforover@gmail.com',
            'password': '25111965q',
            'password2': '25111965q',
            'username': 'Evgen',
            'company': 'some_company',
            'position': 'developer',
            'type': 'buyer'}


@pytest.fixture
def products_list_factory():
    def factory(**kwargs):
        return baker.make('Category', **kwargs)
    return factory


@pytest.fixture
def product_cart_factory():
    def factory(**kwargs):
        category = baker.make('Category')
        return baker.make('Product', category=category, **kwargs)
    return factory


@pytest.fixture
def product_create_factory():
    def factory(**kwargs):
        shop = baker.make('Shop')
        category = baker.make('Category')
        product = baker.make('Product', category=category)
        return baker.make('ProductInfo', product=product, shop=shop, **kwargs)
    return factory


@pytest.fixture
def basket_data(client, product_create_factory):
    product = product_create_factory(quantity=2)
    data = [{'product': product.product_id, 'quantity': product.quantity}]
    return data
