from django.urls import path
from rest_framework.routers import DefaultRouter

from api.views import PartnerUpdate, UserRegistration, LoginAccount

r = DefaultRouter()
r.register('registration', UserRegistration)
urlpatterns = r.urls
urlpatterns += [path('upload2/', PartnerUpdate.as_view())]
urlpatterns += [path('login/', LoginAccount.as_view())]
