from django.urls import path

from . import views

app_name = "client_links"

urlpatterns = [
    path("solicitar/", views.request_client_link, name="request"),
    path("mis-vinculaciones/", views.client_link_list, name="list"),
]