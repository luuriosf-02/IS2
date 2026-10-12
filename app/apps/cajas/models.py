"""SCRUM-11: sesiones, saldos y auditoría de caja por cajero."""
import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class Caja(models.Model):
    cajero = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cajas')
    apertura = models.DateTimeField(auto_now_add=True)
    cierre = models.DateTimeField(null=True, blank=True)
    observacion_apertura = models.TextField(blank=True)
    observacion_cierre = models.TextField(blank=True)

    class Meta:
        ordering = ['-apertura']
        constraints = [models.UniqueConstraint(fields=['cajero'], condition=Q(cierre__isnull=True), name='una_caja_abierta_por_cajero')]

    def __str__(self):
        return f'Caja {self.pk} - {self.cajero}'


class SaldoCaja(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='saldos')
    moneda = models.ForeignKey('divisas.Moneda', on_delete=models.PROTECT)
    inicial = models.DecimalField(max_digits=18, decimal_places=2)
    actual = models.DecimalField(max_digits=18, decimal_places=2)
    contado = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    @property
    def diferencia(self):
        return None if self.contado is None else self.contado - self.actual

    class Meta:
        ordering = ['moneda__codigo']
        constraints = [
            models.UniqueConstraint(fields=['caja', 'moneda'], name='saldo_unico_caja_moneda'),
            models.CheckConstraint(check=Q(inicial__gte=0) & Q(actual__gte=0), name='saldos_caja_no_negativos'),
            models.CheckConstraint(check=Q(contado__isnull=True) | Q(contado__gte=0), name='conteo_caja_no_negativo'),
        ]


class MovimientoCaja(models.Model):
    INGRESO = 'ingreso'
    EGRESO = 'egreso'
    TIPOS = [(INGRESO, 'Ingreso'), (EGRESO, 'Egreso')]
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='movimientos')
    moneda = models.ForeignKey('divisas.Moneda', on_delete=models.PROTECT)
    tipo = models.CharField(max_length=7, choices=TIPOS)
    monto = models.DecimalField(max_digits=18, decimal_places=2)
    concepto = models.CharField(max_length=255)
    referencia = models.CharField(max_length=100, blank=True)
    # Evita duplicar el movimiento al reenviar el mismo formulario.
    clave = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='movimientos_caja')
    fecha = models.DateTimeField(auto_now_add=True)
    anulado_en = models.DateTimeField(null=True, blank=True)
    anulado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='anulaciones_caja')
    motivo_anulacion = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha', '-pk']
        constraints = [
            models.CheckConstraint(check=Q(monto__gt=0), name='movimiento_caja_positivo'),
            models.CheckConstraint(check=Q(tipo__in=['ingreso', 'egreso']), name='tipo_movimiento_caja_valido'),
        ]
