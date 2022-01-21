from django.urls import path
from rest_framework.routers import DefaultRouter

from api.views import  PartnerUpdate

r = DefaultRouter()
urlpatterns = r.urls
urlpatterns += [path('upload2/', PartnerUpdate.as_view())]
