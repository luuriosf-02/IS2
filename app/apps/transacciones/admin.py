from django.contrib import admin

from .models import Transaccion


@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = (
        "referencia",
        "cliente",
        "medio_pago",
        "monto",
        "moneda",
        "estado",
        "fecha_creacion",
    )
    list_filter = ("estado", "moneda", "fecha_creacion")
    search_fields = (
        "referencia",
        "identificador",
        "cliente__nombre_razon_social",
        "cliente__documento",
    )
    readonly_fields = (
        "identificador",
        "fecha_creacion",
        "fecha_actualizacion",
    )