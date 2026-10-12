from django.contrib import admin
from .models import Caja, SaldoCaja, MovimientoCaja

class SoloLecturaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Caja)
class CajaAdmin(SoloLecturaAdmin):
    list_display = ['id', 'cajero', 'apertura', 'cierre']
    list_filter = ['cajero']

@admin.register(SaldoCaja)
class SaldoAdmin(SoloLecturaAdmin):
    list_display = ['caja', 'moneda', 'inicial', 'actual', 'contado', 'diferencia']

@admin.register(MovimientoCaja)
class MovimientoAdmin(SoloLecturaAdmin):
    list_display = ['id', 'caja', 'moneda', 'tipo', 'monto', 'fecha', 'anulado_en']
    list_filter = ['tipo', 'moneda']
    search_fields = ['concepto', 'referencia']
