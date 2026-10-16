from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import TasaCambio, Notificacion

@receiver(pre_save, sender=TasaCambio, dispatch_uid='divisas.tasa.anterior')
def recordar_tasa_anterior(sender, instance, using, raw=False, update_fields=None, **kwargs):
    instance._aviso_tasa = None
    if raw:
        return
    if update_fields is not None and not {'moneda', 'moneda_id', 'tasa_compra', 'tasa_venta'}.intersection(update_fields):
        return
    qs = sender.objects.using(using)
    anterior = qs.filter(pk=instance.pk).first() if instance.pk else None
    if anterior is None:
        anterior = qs.filter(moneda_id=instance.moneda_id).order_by('-fecha_actualizacion', '-pk').first()
    compra = Decimal(str(instance.tasa_compra))
    venta = Decimal(str(instance.tasa_venta))
    if anterior and update_fields is not None:
        if 'tasa_compra' not in update_fields:
            compra = anterior.tasa_compra
        if 'tasa_venta' not in update_fields:
            venta = anterior.tasa_venta
    if anterior and (anterior.moneda_id, anterior.tasa_compra, anterior.tasa_venta) == (instance.moneda_id, compra, venta):
        return
    instance._aviso_tasa = (anterior.tasa_compra, anterior.tasa_venta) if anterior else (None, None)


@receiver(post_save, sender=TasaCambio, dispatch_uid='divisas.tasa.notificar')
def notificar_variacion_tasa(sender, instance, using, raw=False, **kwargs):
    anterior = getattr(instance, '_aviso_tasa', None)
    if raw or anterior is None:
        return
    instance._aviso_tasa = None
    instance = sender.objects.using(using).select_related('moneda').get(pk=instance.pk)
    moneda = instance.moneda
    titulo = f'Cotización actualizada: {moneda.codigo}'
    if anterior[0] is None:
        mensaje = (f'Se registró la primera cotización de {moneda.nombre} ({moneda.codigo}).\n'
                   f'Compra: {instance.tasa_compra}\nVenta: {instance.tasa_venta}')
    else:
        mensaje = (f'Cambio de cotización de {moneda.nombre} ({moneda.codigo}).\n'
                   f'Compra: {anterior[0]} → {instance.tasa_compra}\n'
                   f'Venta: {anterior[1]} → {instance.tasa_venta}')
    usuarios = list(get_user_model().objects.using(using).filter(is_active=True).values_list('pk', flat=True))
    Notificacion.objects.using(using).bulk_create([
        Notificacion(usuario_id=pk, titulo=titulo, mensaje=mensaje) for pk in usuarios
    ])
