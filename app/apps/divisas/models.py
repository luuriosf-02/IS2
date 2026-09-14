from django.db import models
from django.conf import settings
from django.db.models.deletion import ProtectedError


class MonedaQuerySet(models.QuerySet):
    def delete(self):
        if self.filter(codigo='PYG').exists():
            raise ProtectedError(
                'La moneda guaraní (PYG) es obligatoria y no se puede eliminar.',
                self.model,
            )
        return super().delete()


class MonedaManager(models.Manager):
    def get_queryset(self):
        return MonedaQuerySet(self.model, using=self._db)


class Moneda(models.Model):
    """SCRUM-33: Gestionar monedas admitidas"""
    codigo = models.CharField(max_length=5, unique=True, help_text="Ej: USD, PYG, BRL")
    nombre = models.CharField(max_length=50)
    simbolo = models.CharField(max_length=5, help_text="Ej: $, ₲, R$")
    activa = models.BooleanField(default=True, help_text="Habilitada en el sistema")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    objects = MonedaManager()

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def delete(self, *args, **kwargs):
        if self.codigo == 'PYG':
            raise ProtectedError(
                'La moneda guaraní (PYG) es obligatoria y no se puede eliminar.',
                self,
            )
        return super().delete(*args, **kwargs)

class TasaCambio(models.Model):
    """SCRUM-34 & SCRUM-35: Configurar y actualizar tasas de compra y venta"""
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name='tasas')
    tasa_compra = models.DecimalField(max_digits=12, decimal_places=4)
    tasa_venta = models.DecimalField(max_digits=12, decimal_places=4)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_modificador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    class Meta:
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"{self.moneda.codigo} - Compra: {self.tasa_compra} / Venta: {self.tasa_venta}"

class Notificacion(models.Model):
    """SCRUM-67: Notificaciones in-app de variación de tasas"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Notificación para {self.usuario} - {self.titulo}"