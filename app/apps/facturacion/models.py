from django.db import models

from apps.transacciones.models import Transaccion


class FacturaElectronica(models.Model):
    TIPO_FACTURA = "factura"
    TIPO_NOTA_CREDITO = "nota_credito"
    TIPOS_DOCUMENTO = [
        (TIPO_FACTURA, "Factura"),
        (TIPO_NOTA_CREDITO, "Nota de crédito"),
    ]

    ESTADO_EMITIENDO = "emitiendo"
    ESTADO_EMITIDA = "emitida"
    ESTADO_ERROR = "error"
    ESTADOS = [
        (ESTADO_EMITIENDO, "Emitiendo"),
        (ESTADO_EMITIDA, "Emitida"),
        (ESTADO_ERROR, "Error"),
    ]

    transaccion = models.ForeignKey(
        Transaccion,
        on_delete=models.PROTECT,
        related_name="documentos_electronicos",
    )
    tipo_documento = models.CharField(
        max_length=12,
        choices=TIPOS_DOCUMENTO,
        default=TIPO_FACTURA,
    )
    numero_documento = models.CharField(max_length=7, unique=True)
    motivo = models.TextField(blank=True)
    stripe_refund_id = models.CharField(max_length=255, blank=True)
    cdc = models.CharField(max_length=44, blank=True)
    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default=ESTADO_EMITIENDO,
    )
    documento = models.JSONField(default=dict)
    respuesta = models.JSONField(default=dict)
    error = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Factura electrónica"
        verbose_name_plural = "Facturas electrónicas"
        constraints = [
            models.UniqueConstraint(
                fields=["transaccion", "tipo_documento"],
                name="unique_transaction_electronic_document_type",
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_documento_display()} {self.numero_documento} - {self.transaccion.referencia}"


class SecuenciaDocumento(models.Model):
    tipo_documento = models.CharField(
        max_length=12,
        choices=FacturaElectronica.TIPOS_DOCUMENTO,
        unique=True,
    )
    siguiente_numero = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.get_tipo_documento_display()}: {self.siguiente_numero}"