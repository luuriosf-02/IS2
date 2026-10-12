import logging

import stripe
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.stripe.services import sync_customer_payment_methods
from apps.users.client_selection import get_selected_client

from .models import MedioPago

logger = logging.getLogger(__name__)


def obtener_cliente_del_usuario(request):

    cliente = get_selected_client(request)
    return cliente if cliente and cliente.activo else None


def render_sin_cliente_activo(request):
    return render(
        request,
        "payments/sin_cliente_activo.html",
        status=403,
    )


@login_required
def lista_medios_pago(request):
    cliente = obtener_cliente_del_usuario(request)
    if cliente is None:
        return render_sin_cliente_activo(request)

    try:
        sync_customer_payment_methods(cliente)
    except stripe.error.StripeError as exc:
        logger.warning(
            "No se pudieron actualizar los medios de pago desde Stripe "
            "para cliente %s (request_id=%s): %s",
            cliente.pk,
            getattr(exc, "request_id", None),
            getattr(exc, "user_message", None) or str(exc),
        )
        messages.warning(
            request,
            "No se pudieron actualizar las tarjetas desde Stripe. "
            "Se muestran los últimos datos disponibles.",
        )

    medios_pago = MedioPago.objects.filter(
        cliente=cliente,
        stripe_payment_method_id__isnull=False,
    )

    return render(
        request,
        "payments/lista.html",
        {
            "cliente": cliente,
            "medios_pago": medios_pago,
        },
    )

