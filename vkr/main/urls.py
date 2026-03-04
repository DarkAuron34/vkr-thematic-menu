from django.urls import path, include
from django.contrib import admin
from .import views


urlpatterns = [
    path('', views.search, name='home'),
    # path('', views.generate_menu, name='home'),
    path('about/', views.about, name='about'),
    path('menu/', views.menu, name='menu'),
    # path('active_menu/', views.active_menu, name='active_menu'),
    # path('menus/<int:pk>', views.menu_details, name='menu_details'),
    path('restaurants/', views.restaurants, name='restaurants'),
    path('restaurants/<int:pk>/', views.restaurant_details, name='restaurant_details'),
    path('dish/<int:pk>/', views.dish, name='dishes'),
    path('dish_create/', views.dish_create, name='dish_create'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/registration/', views.registration, name='registration'),

    path('favorites/', views.favorites, name='favorites'),
    path('active_menu/set/', views.active_menu_set, name='active_menu_set'),
    path('active_menu/edit/', views.active_menu_edit, name='active_menu_edit'),
    path('active_menu/remove/', views.active_menu_remove, name='active_menu_remove'),
]
