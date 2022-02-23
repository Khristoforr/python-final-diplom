from django.urls import path
from rest_framework.routers import DefaultRouter
from api.views import PartnerUpdate, UserRegistration, LoginAccount, ProductsViewSet, ProductInfoViewSet, BasketViewSet, \
    OrderViewSet, ContactViewSet, ConfirmAccount
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

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
urlpatterns += [path('api/schema/', SpectacularAPIView.as_view(), name='schema')]
urlpatterns += [path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui')]
urlpatterns += [path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc')]