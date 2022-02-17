import json
import pytest
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from api.models import Order, Contact


# проверка вывода списка продуктов, используем фабрику для создания двух категорий.
@pytest.mark.django_db
def test_view_products(client, products_list_factory):
    products_list_factory(_quantity=2)
    url = '/api/v1/products/'
    resp = client.get(url)
    assert len(resp.data) == 2
    assert resp.status_code == 200


# проверка регистрации пользователей
@pytest.mark.django_db
def test_user_registration(client, user_info):
    url = '/api/v1/registration/'
    resp = client.post(url, data=user_info)
    assert resp.status_code == 201


# провера регистрации пользователей с пустыми параметрами
@pytest.mark.parametrize(
    ["parameter", "expected_status"],
    (
            ("email", HTTP_400_BAD_REQUEST),
            ('password', HTTP_400_BAD_REQUEST),
            ('password2', HTTP_400_BAD_REQUEST),
            ('username', HTTP_400_BAD_REQUEST),
            ('type', HTTP_400_BAD_REQUEST),
            ('company', HTTP_201_CREATED),
            ('position', HTTP_201_CREATED),
    )
)
@pytest.mark.django_db
def test_user_registration_with_empty_fields(client, user_info, parameter, expected_status):
    url = '/api/v1/registration/'
    user_info[parameter] = ''
    resp = client.post(url, data=user_info)
    assert resp.status_code == expected_status


# тест просмотра карточки продукта
@pytest.mark.django_db
def test_view_product_cart(client, product_cart_factory):
    product = product_cart_factory()
    url = f"/api/v1/product/{product.id}/"
    resp = client.get(url)
    assert resp.status_code == 200


# тест работы с корзиной товаров для незарегистрированных пользователей.
@pytest.mark.django_db
def test_cart_without_authentication(client):
    url = '/api/v1/basket/'
    resp = client.post(url)
    assert resp.status_code == 401


# добавление товара в корзину
@pytest.mark.django_db
def test_put_smth_in_cart(basket_data, client, user_token, url='/api/v1/basket/'):
    resp = client.post(url, json.dumps(basket_data), content_type="application/json")
    assert resp.status_code == 200
    assert resp.json()['Status'] == True


# получение товаров из корзины
@pytest.mark.django_db
def test_get_products_from_cart(basket_data, client, user_token, url='/api/v1/basket/'):
    client.post(url, json.dumps(basket_data), content_type="application/json")
    resp = client.get(url)
    assert resp.status_code == 200


# редактирование количества товара в корзине
@pytest.mark.django_db
def test_change_quantity_in_cart(basket_data, client, user_token, url='/api/v1/basket/'):
    client.post(url, json.dumps(basket_data), content_type="application/json")
    [basket_data[i].update(quantity=1) for i in range(len(basket_data))]
    resp = client.put(url, json.dumps(basket_data), content_type="application/json")
    assert resp.status_code == 200
    assert resp.json()['Status'] == True


# # удаление товара из корзины
@pytest.mark.django_db
def test_delete_product_in_cart(basket_data, client, user_token, url='/api/v1/basket/'):
    client.post(url, json.dumps(basket_data), content_type="application/json")
    resp = client.delete(url, data={'items': [basket_data[0]['product']]})
    assert resp.status_code == 200
    assert resp.json()['Удалено объектов'] == 1


# проверка размещения заказа без создания контактов пользователя
@pytest.mark.django_db
def test_place_order_without_contacts(basket_data, client, user_token, url='/api/v1/basket/'):
    client.post(url, json.dumps(basket_data), content_type="application/json")
    order = Order.objects.filter(id=1)[0]
    assert order.status == 'basket'
    resp = client.post('/api/v1/orders/', data={'id': order.id})
    assert resp.json()['Status'] == False


# проверка размещения заказа
@pytest.mark.django_db
def test_place_order(basket_data, client, user_token, url='/api/v1/basket/'):
    client.post(url, json.dumps(basket_data), content_type="application/json")
    order = Order.objects.filter(id=1)[0]
    assert order.status == 'basket'
    Contact.objects.create(user_id=1, type='phone', value='89829660332')
    resp = client.post('/api/v1/orders/', data={'id': order.id})
    assert resp.json()['Status'] == True
    assert Order.objects.filter(id=1)[0].status == 'new'


# просмотр всех заказов пользователя
@pytest.mark.django_db
def test_list_orders(basket_data, client, user_token, url='/api/v1/basket/'):
    client.post(url, json.dumps(basket_data), content_type="application/json")
    resp = client.get('/api/v1/orders/')
    assert resp.status_code == 200
