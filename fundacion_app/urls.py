from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('donantes/nuevo/', views.registrar_donante, name='registrar_donante'),
]