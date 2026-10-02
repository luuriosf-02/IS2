from django.urls import path

from . import views


app_name = "transacciones"

urlpatterns = [
    path("historial/", views.historial_transacciones, name="historial"),
    path("crear/", views.crear_transaccion, name="crear"),
]