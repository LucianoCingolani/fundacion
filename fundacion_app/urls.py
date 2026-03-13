from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('donantes/nuevo/', views.registrar_donante, name='registrar_donante'),
    path('donantes/', views.lista_donantes, name='lista_donantes'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('donaciones/nueva/', views.registrar_donacion, name='registrar_donacion'),
    path('comunicacion/enviar/', views.enviar_mail_masivo, name='enviar_mail_masivo'),
]