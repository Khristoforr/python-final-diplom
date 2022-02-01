import yaml
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from yaml import load as load_yaml, Loader
from django.core.validators import URLValidator
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from api.filters import ShopFilter
from api.models import Shop, Category, ProductInfo, Product, Parameter, ProductParameter, User, Order, OrderItem, \
    Contact, ConfirmEmailToken
from api.serializers import UserSerializer, ProductListSerializer, ProductSerializer, OrderSerializer, \
    OrderItemSerializer, ContactSerializer
from api.signals import new_user_registered, new_order


class UserRegistration(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['post', ]

    def perform_create(self, serializer):
        serializer.save()
        user_id = User.objects.order_by('id').last().id
        new_user_registered.send(sender=self.__class__, user_id=user_id)


class LoginAccount(APIView):
    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        filename = request.data.get('filename')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content
                data = load_yaml(stream, Loader=Loader)
                shop, _ = Shop.objects.get_or_create(name=data['shop'], owner_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        elif filename:
            _, file = request.FILES.popitem()
            shop = Shop()
            shop.filename = file[0]
            shop.url = shop.filename.url
            shop.save()
            with open(f'media/{shop.filename}', 'r') as stream:
                try:
                    shop_data = yaml.safe_load(stream)
                    Shop.objects.filter(filename=shop.filename).update(name=shop_data['shop'], owner_id=request.user.id)
                    for category in shop_data['categories']:
                        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                        category_object.shops.add(shop.pk)
                        category_object.save()
                    ProductInfo.objects.filter(shop_id=shop.pk).delete()
                    for item in shop_data['goods']:
                        product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
                        product_info = ProductInfo.objects.create(product_id=product.id,
                                                                  model=item['model'],
                                                                  price=item['price'],
                                                                  price_rrc=item['price_rrc'],
                                                                  quantity=item['quantity'],
                                                                  shop_id=shop.pk)
                        for name, value in item['parameters'].items():
                            parameter_object, _ = Parameter.objects.get_or_create(name=name)
                            ProductParameter.objects.create(product_info_id=product_info.id,
                                                            parameter_id=parameter_object.id,
                                                            value=value)
                except yaml.YAMLError as exc:
                    return JsonResponse({'Status': False, 'Error': str(exc)})

            return JsonResponse({'Status': True})

        else:
            return JsonResponse({'Status': False, 'Errors': 'Необходимо указать либо URL с файлом каталога магазина, '
                                                            'либо прикрепить файл yaml.'})


class ProductsViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = ProductListSerializer
    http_method_names = ['get', ]
    filterset_class = ShopFilter


class ProductInfoViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    http_method_names = ['get', ]

    def get_queryset(self):
        queryset = Product.objects.filter(id=self.kwargs.get('id'))
        return queryset


class BasketViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.filter(user_id=self.request.user.id, status='basket').\
            prefetch_related('ordered_items').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        if self.request.data:
            try:
                objects_created = 0
                order, _ = Order.objects.get_or_create(user_id=self.request.user.id, status='basket')
                for product in self.request.data:
                    serializer = OrderItemSerializer(data=product)
                    if serializer.is_valid():
                        try:
                            serializer.save(order_id=order.id)
                            objects_created += 1
                        except IntegrityError:
                            return JsonResponse({'Status': False, 'Возникла ошибка!': "Товар уже находится в корзине"})
                    else:
                        return JsonResponse({'Status': False, 'Возникла ошибка!': serializer.errors})
                return JsonResponse({'Status': True, 'Добавлено объектов': objects_created})
            except TypeError:
                return JsonResponse({'Status': False, 'Возникла ошибка!': "Некорректный формат данных"})
        return JsonResponse({'Status': False, 'Возникла ошибка!': "Указаны не все аргументы"})

    @action(methods=['delete'], detail=False)
    def delete(self, request, *args, **kwargs):
        products_to_delete = str(self.request.data['items']).split(',')
        if products_to_delete:
            basket, _ = Order.objects.get_or_create(user_id=self.request.user.id, status='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in products_to_delete:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, product_id=order_item_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                if deleted_count != 0:
                    return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
                else:
                    return JsonResponse({'Status': False, 'Errors': 'Укажите корректные товары для удаления'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    @action(methods=['put'], detail=False)
    def put(self, request, *args, **kwargs):
        if self.request.data:
            try:
                objects_updated = 0
                basket, _ = Order.objects.get_or_create(user_id=self.request.user.id, status='basket')
                for product in self.request.data:
                    product.update(order_id=basket.id)
                    serializer = OrderItemSerializer(data=product)
                    if serializer.is_valid():
                        if type(product['product']) == int and type(product['quantity']) == int:
                            objects_updated += OrderItem.objects.filter(order_id=basket.id,
                                                                        product_id=product['product']).update(
                                quantity=product['quantity'])
                    else:
                        return JsonResponse({'Status': False, 'Возникла ошибка!': serializer.errors})
                return JsonResponse({"Status": True, "Обновлено объектов": objects_updated})
            except ValueError:
                return JsonResponse({'Status': False, 'Возникла ошибка!': "Некорректный формат данных"})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.filter(user_id=self.request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        if {'id'}.issubset(self.request.data):
            if self.request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(id=self.request.data['id']).update(status='new')
                except IntegrityError:
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        user_info = User.objects.filter(id=self.request.user.id).first()
                        phone = Contact.objects.filter(user_id=self.request.user.id, type='phone').first()
                        total_sum = Order.objects.filter(id=self.request.data['id']).prefetch_related(
                            'ordered_items').annotate(
                            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))
                        ).distinct()[0].total_sum
                        if phone:
                            new_order.send(sender=self.__class__, user_id=self.request.user.id,
                                           order_id=self.request.data['id'],
                                           )
                            return JsonResponse({'Status': True,
                                                 "last_name": user_info.last_name,
                                                 "first_name": user_info.first_name,
                                                 "email": user_info.email,
                                                 "phone": phone.value,
                                                 "total_sum": total_sum
                                                 })

                        else:
                            return JsonResponse({'Status': False, 'Errors': 'Укажите контактный номер для связи'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Contact.objects.filter(user_id=self.request.user.id)
        return queryset

    @action(methods=['delete'], detail=False)
    def delete(self, request, *args, **kwargs):
        try:
            contacts_to_delete = str(self.request.data['items']).split(',')
            if contacts_to_delete:
                query = Q()
                objects_deleted = False
                for contact_id in contacts_to_delete:
                    if contact_id.isdigit():
                        query = query | Q(user_id=request.user.id, id=contact_id)
                        objects_deleted = True
                if objects_deleted:
                    deleted_count = Contact.objects.filter(query).delete()[0]
                    return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
            return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
        except KeyError:
            return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    @action(methods=['put'], detail=False)
    def put(self, request, *args, **kwargs):
        if 'id' in self.request.data:
            if self.request.data['id'].isdigit():
                contact = Contact.objects.filter(id=self.request.data['id'], user_id=self.request.user.id).first()
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({"Status": True})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    def perform_create(self, serializer):
        user_id = self.request.user.id
        try:
            serializer.save(user_id=user_id)
        except IntegrityError:
            raise ValidationError({"Status": False, "Errors": "Контакт уже существует"})


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """
    # Регистрация методом POST
    def post(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
