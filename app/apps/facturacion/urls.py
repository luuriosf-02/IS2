from django.urls import path

from . import views


app_name = "facturacion"

urlpatterns = [
    path(
        "transacciones/<int:transaccion_id>/nota-credito/",
        views.solicitar_nota_credito,
        name="solicitar_nota_credito",
    ),
    path(
        "documentos/<int:factura_id>/<str:formato>/",
        views.descargar_documento,
        name="descargar",
    ),
]