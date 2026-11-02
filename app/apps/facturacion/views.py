import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

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