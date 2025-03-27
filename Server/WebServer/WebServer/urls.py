"""
URL configuration for WebServer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from login import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/<str:name>', views.login, name='login'),
    # For parameters use /<type:name_of_parameter> and go to the function to update the parameters received.
    path('welcome/<str:name>', views.welcome, name='welcome'),
    path('login_failed/', views.login_failed, name='login_failed'),
    path('register/<str:username>/<str:passwd>', views.register, name='register'),
    path('get/', views.get_user, name='get'),
    path('change/<str:username>/<str:old>/<str:new>', views.change_password, name='change_password'),
    path('deck_save_view/', views.save_deck, name='save_deck'),
    path('deck_creation_view/', views.deck_creation_view, name='deck_creation'),
    path('deck_creation_form/', views.deck_creation_form, name='deck_creation_form'),
]
