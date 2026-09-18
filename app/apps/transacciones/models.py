import uuid

from django.core.validators import MinValueValidator
from django.db import models

from apps.clientes.models import Cliente
from apps.divisas.models import Moneda
from apps.payments.models import MedioPago


class Transaccion(models.Model):
    """Registro de una operación de pago realizada por un cliente."""

    ESTADO_PENDIENTE = "pendiente"
    ESTADO_PAGADA = "pagada"
    ESTADO_ANULADA = "anulada"
    ESTADO_CANCELADA = "cancelada"

    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_PAGADA, "Pagada"),
        (ESTADO_ANULADA, "Anulada"),
        (ESTADO_CANCELADA, "Cancelada"),
    ]

    TIPO_COMPRA = "compra"
    TIPO_VENTA = "venta"
    TIPO_OPERACION_CHOICES = [
        (TIPO_COMPRA, "Compra"),
        (TIPO_VENTA, "Venta"),
    ]

    identificador = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Identificador",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="transacciones",
        verbose_name="Cliente",
    )
    medio_pago = models.ForeignKey(
        MedioPago,
        on_delete=models.PROTECT,
        related_name="transacciones",
        verbose_name="Medio de pago",
    )
    monto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Monto",
    )
    cantidad_divisa = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        null=True,
        blank=True,
        verbose_name="Cantidad en divisa",
    )
    divisa = models.ForeignKey(
        Moneda,
        on_delete=models.PROTECT,
        related_name="transacciones_extranjeras",
        null=True,
        blank=True,
        verbose_name="Divisa operada",
    )
    tipo_operacion = models.CharField(
        max_length=6,
        choices=TIPO_OPERACION_CHOICES,
        null=True,
        blank=True,
        verbose_name="Tipo de operación",
    )
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.PROTECT,
        related_name="transacciones",
        verbose_name="Moneda",
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
        verbose_name="Estado",
    )
    referencia = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Referencia",
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descripción",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    fecha_finalizacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de finalización",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización",
    )

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"

    def __str__(self):
        return f"{self.referencia} - {self.monto} {self.moneda.codigo}"