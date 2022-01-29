from django.urls import path
from rest_framework.routers import DefaultRouter

from api.views import PartnerUpdate, UserRegistration, LoginAccount, ProductsViewSet, ProductInfoViewSet, BasketViewSet

r = DefaultRouter()
r.register('registration', UserRegistration)
r.register('products', ProductsViewSet)
r.register(r'product/(?P<id>\w+)', ProductInfoViewSet)
r.register('basket', BasketViewSet)
urlpatterns = r.urls
urlpatterns += [path('upload2/', PartnerUpdate.as_view())]
urlpatterns += [path('login/', LoginAccount.as_view())]
