import yaml
from django.contrib.auth import authenticate
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from yaml import load as load_yaml, Loader
from django.core.validators import URLValidator
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from api.models import Shop, Category, ProductInfo, Product, Parameter, ProductParameter, User
from api.serializers import UserSerializer


class UserRegistration(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['post', ]


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
                # shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                shop, _ = Shop.objects.get_or_create(name=data['shop'])
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
            print(shop.pk)
            with open(f'media/{shop.filename}', 'r') as stream:
                try:
                    shop_data = yaml.safe_load(stream)
                    Shop.objects.filter(filename=shop.filename).update(name=shop_data['shop'])
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
