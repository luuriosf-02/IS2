from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import TasaCambio, Notificacion

User = get_user_model()

@receiver(post_save, sender=TasaCambio)
def notificar_variacion_tasa(sender, instance, created, **kwargs):
    """
    SCRUM-67: Dispara notificaciones in-app y por correo electrónico 
    a los usuarios cuando se registra o modifica una tasa de cambio.
    """
    accion = "configurado" if created else "actualizado"
    titulo = f"Variación en la Tasa de Cambio: {instance.moneda.codigo}"
    mensaje = (
        f"Se han {accion} las tasas para la moneda {instance.moneda.nombre} ({instance.moneda.codigo}):\n"
        f"- Tasa Compra: {instance.tasa_compra}\n"
        f"- Tasa Venta: {instance.tasa_venta}"
    )

    # 1. Notificación In-App (Creación individual para evitar omisión en transacciones de prueba)
    usuarios = User.objects.filter(is_active=True)
    for usuario in usuarios:
        Notificacion.objects.create(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje
        )

    # 2. Notificación vía Email
    emails_validos = [u.email for u in usuarios if u.email]
    if emails_validos:
        send_mail(
            subject=titulo,
            message=mensaje,
            from_email=None,
            recipient_list=emails_validos,
            fail_silently=True,
        )