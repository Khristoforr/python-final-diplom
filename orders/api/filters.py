import django_filters
from api.models import Shop, Category


class ShopFilter(django_filters.rest_framework.FilterSet):
    class Meta:
        model = Category
        fields = ['name', 'shops__name']