from django.urls import path
from rest_framework.routers import DefaultRouter

from api.views import PartnerUpdate, UserRegistration, LoginAccount, ProductsViewSet, ProductInfoViewSet, BasketViewSet, \
    OrderViewSet, ContactViewSet, ConfirmAccount

r = DefaultRouter()
r.register('registration', UserRegistration)
r.register('products', ProductsViewSet)
r.register(r'product/(?P<id>\w+)', ProductInfoViewSet)
r.register('basket', BasketViewSet)
r.register('orders', OrderViewSet)
r.register('contacts', ContactViewSet)
urlpatterns = r.urls
urlpatterns += [path('upload/', PartnerUpdate.as_view())]
urlpatterns += [path('login/', LoginAccount.as_view())]
urlpatterns += [path('register/confirm', ConfirmAccount.as_view())]