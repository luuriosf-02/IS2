from django.contrib import admin
from .models import Moneda, TasaCambio, Notificacion

@admin.register(Moneda)
class MonedaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'simbolo', 'activa', 'fecha_creacion')
    list_filter = ('activa',)
    search_fields = ('codigo', 'nombre')

@admin.register(TasaCambio)
class TasaCambioAdmin(admin.ModelAdmin):
    list_display = ('moneda', 'tasa_compra', 'tasa_venta', 'fecha_actualizacion', 'usuario_modificador')
    list_filter = ('moneda', 'fecha_actualizacion')
    search_fields = ('moneda__codigo', 'moneda__nombre')

    def save_model(self, request, obj, form, change):
        if not obj.usuario_modificador:
            obj.usuario_modificador = request.user
        super().save_model(request, obj, form, change)

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'titulo', 'leida', 'fecha_creacion')
    list_filter = ('leida', 'fecha_creacion')
    search_fields = ('usuario__username', 'titulo', 'mensaje')
