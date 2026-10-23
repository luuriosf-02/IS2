"""SCRUM-11: sesiones, saldos y auditoría de caja por cajero."""
import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class Caja(models.Model):
    cajero = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cajas')
    abierta_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='cajas_abiertas')
    apertura = models.DateTimeField(auto_now_add=True)
    cierre = models.DateTimeField(null=True, blank=True)
    aceptada_en = models.DateTimeField(null=True, blank=True)
    aceptada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='cajas_aceptadas')
    apertura_anterior = models.BooleanField(default=False, editable=False)
    observacion_apertura = models.TextField(blank=True)
    observacion_cierre = models.TextField(blank=True)

    class Meta:
        ordering = ['-apertura']
        constraints = [models.UniqueConstraint(fields=['cajero'], condition=Q(cierre__isnull=True), name='una_caja_abierta_por_cajero')]

    @property
    def habilitada(self):
        return self.aceptada_en is not None or self.apertura_anterior

    @property
    def estado(self):
        if self.cierre is not None:
            return 'Cerrada'
        if self.apertura_anterior:
            return 'Abierta (anterior a aceptación)'
        return 'Abierta' if self.habilitada else 'Pendiente de aceptación'

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
    cambio = models.ForeignKey('CambioCaja', on_delete=models.PROTECT, null=True, blank=True, related_name='movimientos')
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
            models.UniqueConstraint(fields=['cambio', 'tipo'], name='un_movimiento_por_tipo_cambio'),
        ]


class CambioCaja(models.Model):
    """Cambio presencial de efectivo; conserva los importes y la cotización aplicada."""
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='cambios')
    moneda_recibida = models.ForeignKey('divisas.Moneda', on_delete=models.PROTECT, related_name='+')
    moneda_entregada = models.ForeignKey('divisas.Moneda', on_delete=models.PROTECT, related_name='+')
    monto_recibido = models.DecimalField(max_digits=18, decimal_places=2)
    monto_entregado = models.DecimalField(max_digits=18, decimal_places=2)
    tasa = models.DecimalField(max_digits=12, decimal_places=4)
    tipo_tasa = models.CharField(max_length=6, choices=[('compra', 'Compra'), ('venta', 'Venta')])
    referencia = models.CharField(max_length=100, blank=True)
    clave = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    fecha = models.DateTimeField(auto_now_add=True)
    anulado_en = models.DateTimeField(null=True, blank=True)
    anulado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    motivo_anulacion = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha', '-pk']
        constraints = [
            models.CheckConstraint(check=Q(monto_recibido__gt=0) & Q(monto_entregado__gt=0) & Q(tasa__gt=0), name='cambio_importes_positivos'),
            models.CheckConstraint(check=~Q(moneda_recibida=models.F('moneda_entregada')), name='cambio_monedas_distintas'),
            models.CheckConstraint(check=Q(tipo_tasa__in=['compra', 'venta']), name='cambio_tipo_tasa_valido'),
        ]


class ConteoInicial(models.Model):
    """Cada intento de aceptación conserva un registro del efectivo contado."""
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='conteos_iniciales')
    cajero = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    fecha = models.DateTimeField(auto_now_add=True)
    coincide = models.BooleanField()
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha', '-pk']


class DetalleConteoInicial(models.Model):
    conteo = models.ForeignKey(ConteoInicial, on_delete=models.PROTECT, related_name='detalles')
    moneda = models.ForeignKey('divisas.Moneda', on_delete=models.PROTECT)
    asignado = models.DecimalField(max_digits=18, decimal_places=2)
    contado = models.DecimalField(max_digits=18, decimal_places=2)

    @property
    def diferencia(self):
        return self.contado - self.asignado

    class Meta:
        ordering = ['moneda__codigo']
        constraints = [
            models.UniqueConstraint(fields=['conteo', 'moneda'], name='conteo_inicial_moneda_unica'),
            models.CheckConstraint(check=Q(asignado__gte=0) & Q(contado__gte=0), name='conteo_inicial_no_negativo'),
        ]
