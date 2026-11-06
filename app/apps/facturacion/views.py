import logging
from datetime import timedelta

import requests
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.stripe.services import refund_transaction
from apps.transacciones.models import Transaccion
from apps.users.client_selection import get_selected_client

from . import services
from .models import FacturaElectronica


logger = logging.getLogger(__name__)
ESTADOS_SIFEN_APROBADOS = {"Aprobado", "Aprobado con observación"}


def _volver_al_historial_con_aviso(request, factura, motivo):
    textos = {
        "pendiente": "SIFEN todavía no la aprobó; intenta nuevamente más tarde.",
        "cancelada": "SIFEN indica que fue cancelada o inutilizada y no se puede descargar.",
        "error": "no se pudo verificar o descargar desde Factura Segura; intenta nuevamente.",
    }
    messages.warning(
        request,
        f"Transacción {factura.transaccion.referencia}: "
        f"{textos[motivo]}",
        extra_tags="invoice-availability",
    )
    return redirect("transacciones:historial")


@login_required
def descargar_documento(request, factura_id, formato):
    if formato not in {"kude", "xml"}:
        return HttpResponse(status=404)

    cliente = get_selected_client(request)
    if cliente is None or not cliente.activo:
        return HttpResponse(status=403)

    factura = get_object_or_404(
        FacturaElectronica.objects.select_related("transaccion"),
        pk=factura_id,
        transaccion__cliente=cliente,
        estado=FacturaElectronica.ESTADO_EMITIDA,
    )
    if not factura.cdc:
        return _volver_al_historial_con_aviso(request, factura, "error")

    try:
        estado = services.get_estado_sifen(factura.cdc, settings.FS_D_RUC_EM)
        resultados = estado.get("results") or []
        detalle = resultados[0] if resultados and isinstance(resultados[0], dict) else {}
        estado_sifen = detalle.get("estado_sifen")
        evento_final = detalle.get("estado_can") == "Aprobado" or detalle.get("estado_inu") == "Aprobado"
        if estado_sifen not in ESTADOS_SIFEN_APROBADOS or evento_final:
            motivo = "cancelada" if evento_final else "pendiente"
            return _volver_al_historial_con_aviso(request, factura, motivo)

        contenido = (
            services.dwn_kude(settings.FS_D_RUC_EM, factura.cdc)
            if formato == "kude"
            else services.dwn_xml(settings.FS_D_RUC_EM, factura.cdc)
        )
    except (services.FacturaSeguraError, requests.RequestException) as error:
        logger.warning(
            "No se pudo verificar o descargar el documento fiscal %s: %s",
            factura.pk,
            error,
        )
        return _volver_al_historial_con_aviso(request, factura, "error")

    extension = "pdf" if formato == "kude" else "xml"
    content_type = "application/pdf" if formato == "kude" else "application/xml"
    response = HttpResponse(contenido, content_type=content_type)
    response["Content-Disposition"] = (
        f'attachment; filename="{formato}-{factura.numero_documento}.{extension}"'
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_POST
def solicitar_nota_credito(request, transaccion_id):
    cliente = get_selected_client(request)
    if cliente is None or not cliente.activo:
        return HttpResponse(status=403)

    transaccion = get_object_or_404(
        Transaccion.objects
        .select_related("cliente", "medio_pago", "divisa"),
        pk=transaccion_id,
        cliente=cliente,
        estado="pagada",
    )
    motivo = request.POST.get("motivo", "").strip()
    if len(motivo) < 5 or len(motivo) > 500:
        messages.error(request, "Escribe un motivo de entre 5 y 500 caracteres.")
        return redirect("transacciones:historial")

    ahora = timezone.now()
    fecha_pago = transaccion.fecha_finalizacion
    if fecha_pago is None or fecha_pago > ahora or ahora > fecha_pago + timedelta(days=3):
        messages.error(
            request,
            f"La transacción {transaccion.referencia} está fuera del plazo de 3 días para reembolso.",
        )
        return redirect("transacciones:historial")
    if not transaccion.stripe_payment_intent_id:
        messages.error(
            request,
            f"No se puede reembolsar {transaccion.referencia}: no tiene un PaymentIntent de Stripe registrado.",
        )
        return redirect("transacciones:historial")

    factura_original = FacturaElectronica.objects.filter(
        transaccion=transaccion,
        tipo_documento=FacturaElectronica.TIPO_FACTURA,
        estado=FacturaElectronica.ESTADO_EMITIDA,
    ).exclude(cdc="").first()
    if factura_original is None:
        messages.error(
            request,
            f"No se puede reembolsar {transaccion.referencia}: falta una factura electrónica emitida.",
        )
        return redirect("transacciones:historial")

    nota_existente = FacturaElectronica.objects.filter(
        transaccion=transaccion,
        tipo_documento=FacturaElectronica.TIPO_NOTA_CREDITO,
    ).first()
    if nota_existente is not None:
        messages.info(
            request,
            f"Ya existe una nota de crédito para {transaccion.referencia} "
            f"(estado: {nota_existente.get_estado_display()}).",
        )
        return redirect("transacciones:historial")

    try:
        estado = services.get_estado_sifen(
            factura_original.cdc,
            settings.FS_D_RUC_EM,
        )
        results = estado.get("results") or []
        detalle = results[0] if results and isinstance(results[0], dict) else {}
        estado_sifen = detalle.get("estado_sifen")
        evento_final = (
            detalle.get("estado_can") == "Aprobado"
            or detalle.get("estado_inu") == "Aprobado"
        )
        if estado_sifen not in ESTADOS_SIFEN_APROBADOS or evento_final:
            messages.error(
                request,
                f"No se puede reembolsar {transaccion.referencia}: SIFEN todavía no aprobó la factura original.",
            )
            return redirect("transacciones:historial")

        refund = refund_transaction(transaccion, motivo)
        if refund.status != "succeeded":
            if refund.status in {"pending", "requires_action"}:
                messages.warning(
                    request,
                    f"El reembolso de {transaccion.referencia} sigue pendiente en Stripe; "
                    "la nota se emitirá cuando Stripe lo confirme.",
                )
            else:
                messages.error(
                    request,
                    f"Stripe no pudo completar el reembolso de {transaccion.referencia} "
                    f"(estado: {refund.status}). Contacta con soporte.",
                )
            return redirect("transacciones:historial")

        nota = services.emitir_nota_credito(
            transaccion,
            factura_original.cdc,
            motivo,
            refund.id,
        )
    except (stripe.error.StripeError, ValueError) as error:
        logger.exception("Stripe no pudo reembolsar la transacción %s", transaccion.pk)
        messages.error(
            request,
            f"No se pudo completar el reembolso de {transaccion.referencia}: {error}",
        )
        return redirect("transacciones:historial")
    except (services.FacturaSeguraError, requests.RequestException) as error:
        logger.exception(
            "No se pudo completar la nota de crédito de la transacción %s: %s",
            transaccion.pk,
            error,
        )
        messages.error(
            request,
            f"El reembolso de {transaccion.referencia} pudo procesarse, pero la nota de crédito falló. "
            "Contacta con soporte antes de volver a intentarlo.",
        )
        return redirect("transacciones:historial")

    messages.success(
        request,
        f"Reembolso procesado y nota de crédito {nota.numero_documento} solicitada "
        f"para {transaccion.referencia} (CDC {nota.cdc}).",
    )
    return redirect("transacciones:historial")