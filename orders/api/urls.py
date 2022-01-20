from django.urls import path
from rest_framework.routers import DefaultRouter

from api.views import ShopUpdate, PartnerUpdate

r = DefaultRouter()
r.register('upload', ShopUpdate)
urlpatterns = r.urls
urlpatterns += [path('upload2/', PartnerUpdate.as_view())]
