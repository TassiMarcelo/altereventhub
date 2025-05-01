from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),

    #CATEGORIAS
    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_form, name="category_new"),
    path("categories/<int:id>/edit/", views.category_form, name="category_edit"),
    path("categories/<int:id>/delete/", views.category_delete, name="category_delete"),
]
