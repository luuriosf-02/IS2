from django.urls import path

from . import views


app_name = "payments"

urlpatterns = [
    path(
        "",
        views.lista_medios_pago,
        name="lista",
    ),
]