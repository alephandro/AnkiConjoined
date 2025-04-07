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
from login.api_views import token_auth, verify_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),

    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('welcome/<str:name>', views.welcome, name='welcome'),

    # Deck management
    path('decks/', views.user_decks, name='my_decks'),
    path('decks/create/', views.deck_creation_view, name='deck_creation'),
    path('decks/create/form/', views.deck_creation_form, name='deck_creation_form'),
    path('decks/save/', views.save_deck_local, name='save_deck'),
    path('decks/delete/<str:deck_code>/', views.delete_deck, name='delete_deck'),

    # Additional URL patterns to add to urlpatterns list:
    path('decks/<str:deck_code>/detail/', views.deck_detail, name='deck_detail'),
    path('decks/<str:deck_code>/users/<str:username>/change-role/', views.change_user_role, name='change_user_role'),
    path('decks/<str:deck_code>/users/<str:username>/remove/', views.remove_deck_user, name='remove_deck_user'),
    path('decks/<str:deck_code>/users/add/', views.add_deck_user, name='add_deck_user'),

    # Login API
    path('api/token-auth/', token_auth, name='token_auth'),
    path('api/verify-token/', verify_token, name='verify_token'),
]
