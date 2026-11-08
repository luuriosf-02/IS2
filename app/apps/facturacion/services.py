from urllib.parse import quote
from decimal import Decimal
import json
import re
import shlex

import requests
from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone

from apps.transacciones.models import Transaccion
from apps.users.models import UserClientLink


class FacturaSeguraError(Exception):
    """Base error for Factura Segura requests."""


class FacturaSeguraConfigurationError(FacturaSeguraError):
    """Raised when required Factura Segura configuration is missing."""


class FacturaSeguraAPIError(FacturaSeguraError):
    def __init__(self, code, description, response):
        super().__init__(f"Factura Segura ({code}): {description}")
        self.code = code
        self.response = response


def _required_setting(name):
    value = getattr(settings, name, "")
    if value is None or str(value).strip() == "":
        raise FacturaSeguraConfigurationError(
            f"La variable de entorno {name} no está configurada."
        )
    return str(value).strip()


def _decimal_text(value):
    text = format(Decimal(str(value)).normalize(), "f")
    return text if text not in ("-0", "") else "0"


def _recipient_email(client):
    if getattr(client, "email", ""):
        return client.email
    owner_email = getattr(getattr(client, "creado_por", None), "email", "")
    if owner_email:
        return owner_email
    if not getattr(client, "pk", None):
        return ""
    return (
        UserClientLink.objects.filter(
            client=client,
            status=UserClientLink.STATUS_APPROVED,
        )
        .exclude(user__email="")
        .values_list("user__email", flat=True)
        .first()
        or ""
    )


def _recipient_identity(client):
    document = re.sub(r"[^0-9]", "", client.documento or "")
    if not document:
        raise FacturaSeguraError("El documento de identidad del cliente está vacío.")
    if client.es_contribuyente is None:
        raise FacturaSeguraError(
            "El cliente aún no declaró su condición tributaria al solicitar la vinculación."
        )
    if client.tipo_persona == "FISICA":
        tipo_contribuyente = _required_setting("FS_I_TI_CONT_REC_FISICA")
    elif client.tipo_persona == "JURIDICA":
        tipo_contribuyente = _required_setting("FS_I_TI_CONT_REC_JURIDICA")
    else:
        raise FacturaSeguraError("El tipo de persona del cliente no es válido.")

    if client.es_contribuyente:
        if len(document) < 2:
            raise FacturaSeguraError("El RUC del contribuyente no tiene formato válido.")
        identificacion = {
            "dRucRec": document[:-1],
            "dDVRec": document[-1],
            "iTipIDRec": "0",
            "dNumIDRec": "0",
        }
        naturaleza = _required_setting("FS_I_NAT_REC_CONTRIBUYENTE")
    else:
        identificacion = {
            "dRucRec": "0",
            "dDVRec": "0",
            "iTipIDRec": "1",
            "dNumIDRec": document,
        }
        naturaleza = _required_setting("FS_I_NAT_REC_NO_CONTRIBUYENTE")
    return {
        "iNatRec": naturaleza,
        "iTiContRec": tipo_contribuyente,
        **identificacion,
    }


def build_exchange_invoice(
    transaction,
    invoice_number,
    tipo_documento="factura",
    cdc_referenciado=None,
    motivo_nota="",
):
    """Build the SIFEN summarized DE for a settled currency exchange."""
    if transaction.estado != "pagada" or transaction.medio_pago_id is None:
        raise FacturaSeguraError("Solo se puede facturar una transacción pagada con medio de pago.")
    if transaction.tipo_operacion not in ("compra", "venta"):
        raise FacturaSeguraError("La transacción no contiene una operación de cambio válida.")
    if not transaction.divisa or not transaction.cantidad_divisa:
        raise FacturaSeguraError("La transacción no contiene la divisa y cantidad operadas.")
    document_type_settings = {
        "factura": "DS_I_TI_DE_FACTURA",
        "nota_credito": "DS_I_TI_DE_NOTA",
    }
    try:
        document_type_setting = document_type_settings[tipo_documento]
    except KeyError as error:
        raise FacturaSeguraError("El tipo de documento fiscal no es válido.") from error
    if tipo_documento == "nota_credito" and not cdc_referenciado:
        raise FacturaSeguraError("La nota de crédito requiere el CDC de la factura original.")
    if tipo_documento == "nota_credito" and not motivo_nota.strip():
        raise FacturaSeguraError("La nota de crédito requiere un motivo.")

    client = transaction.cliente
    email = _recipient_email(client)
    if not email:
        raise FacturaSeguraError("El cliente no tiene un email válido para recibir la factura.")
    identity = _recipient_identity(client)
    medio_pago = transaction.medio_pago
    if medio_pago.marca not in {"VISA", "MASTERCARD", "AMEX", "OTRA"}:
        raise FacturaSeguraError("La marca del medio de pago no se puede facturar.")
    payment_type = {
        "TARJETA": "3",
        "CREDITO": "3",
        "DEBITO": "4",
    }.get(medio_pago.tipo)
    if payment_type is None:
        raise FacturaSeguraError("Factura Segura no admite este tipo de medio de pago.")

    amount = Decimal(transaction.monto)
    quantity = Decimal(transaction.cantidad_divisa)
    rate = amount / quantity
    now = timezone.localtime()
    description = (
        f"Cambio de divisas: {transaction.tipo_operacion.upper()} de "
        f"{_decimal_text(quantity)} {transaction.divisa.codigo}; "
        f"tipo de cambio {_decimal_text(rate)} PYG por {transaction.divisa.codigo}; "
        f"referencia {transaction.referencia}; pago con tarjeta "
        f"{medio_pago.marca} terminada en {medio_pago.ultimos_cuatro}"
    )[:255]

    tipo_operacion_setting = (
        "FS_I_TIP_TRA_COMPRA"
        if transaction.tipo_operacion == "compra"
        else "FS_I_TIP_TRA_VENTA"
    )
    operacion_comercial_setting = (
        "FS_I_TI_OPE_B2C"
        if client.tipo_persona == "FISICA"
        else "FS_I_TI_OPE_B2B"
    )
    document = {
        "iTipEmi": "1",
        "iTiDE": _required_setting(document_type_setting),
        "dNumTim": _required_setting("FS_D_NUM_TIM"),
        "dFeIniT": _required_setting("FS_D_FE_INI_T"),
        "dEst": _required_setting("FS_D_EST"),
        "dPunExp": _required_setting("FS_D_PUN_EXP"),
        "dNumDoc": str(invoice_number).zfill(7),
        "dFeEmiDE": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "CDC": "0",
        "dCodSeg": "0",
        "dDVId": "0",
        "dSisFact": "1",
        "iTipTra": _required_setting(tipo_operacion_setting),
        "iTImp": _required_setting("FS_I_T_IMP"),
        "cMoneOpe": "PYG",
        "dCondTiCam": "1",
        "dTiCam": "1",
        "dRucEm": _required_setting("FS_D_RUC_EM"),
        "dDVEmi": _required_setting("FS_DV_EMI"),
        "iTipCont": _required_setting("FS_I_TIP_CONT"),
        "dNomEmi": _required_setting("FS_D_NOM_EMI"),
        "dDirEmi": _required_setting("FS_D_DIR_EMI"),
        "dNumCas": _required_setting("FS_D_NUM_CAS"),
        "cDepEmi": _required_setting("FS_C_DEP_EMI"),
        "dDesDepEmi": _required_setting("FS_D_DES_DEP_EMI"),
        "cCiuEmi": _required_setting("FS_C_CIU_EMI"),
        "dDesCiuEmi": _required_setting("FS_D_DES_CIU_EMI"),
        "dTelEmi": _required_setting("FS_D_TEL_EMI"),
        "dEmailE": _required_setting("FS_D_EMAIL_E"),
        "gActEco": [
            {
                "cActEco": _required_setting("FS_C_ACT_ECO1"),
                "dDesActEco": _required_setting("FS_D_DES_ACT_ECO1"),
            },
            {
                "cActEco": _required_setting("FS_C_ACT_ECO2"),
                "dDesActEco": _required_setting("FS_D_DES_ACT_ECO2"),
            },
        ],
        **identity,
        "iTiOpe": _required_setting(operacion_comercial_setting),
        "cPaisRec": "PRY",
        "dNomRec": client.nombre_razon_social,
        "dEmailRec": email,
        "iIndPres": _required_setting("FS_I_IND_PRES"),
        "iCondOpe": "1",
        "gPaConEIni": [
            {
                "iTiPago": payment_type,
                "dMonTiPag": _decimal_text(amount),
                "cMoneTiPag": "PYG",
                "dTiCamTiPag": "1",
                "iForProPa": _required_setting("FS_I_FOR_PRO_PA"),
                "iDenTarj": _required_setting(
                    f"FS_I_DEN_TARJ_{medio_pago.marca}"
                ),
            }
        ],
        "iCondCred": "1",
        "dPlazoCre": "0",
        "gCamItem": [
            {
                "dCodInt": f"CAMBIO-{transaction.pk}",
                "dDesProSer": description,
                "cUniMed": "77",
                "dCantProSer": "1",
                "dPUniProSer": _decimal_text(amount),
                "dDescItem": "0",
                "dDescGloItem": "0",
                "dAntPreUniIt": "0",
                "dAntGloPreUniIt": "0",
                "iAfecIVA": _required_setting("FS_I_AFEC_IVA"),
                "dPropIVA": _required_setting("FS_D_PROP_IVA"),
                "dTasaIVA": _required_setting("FS_D_TASA_IVA"),
            }
        ],
    }
    if tipo_documento == "nota_credito":
        document["iMotEmi"] = _required_setting("FS_I_MOT_EMI_NOTA")
        document["dInfAdic"] = motivo_nota.strip()[:500]
        document["gCamDEAsoc"] = [
            {
                "iTipDocAso": "1",
                "dCdCDERef": cdc_referenciado,
                "dNTimDI": "0",
                "dEstDocAso": "0",
                "dPExpDocAso": "0",
                "dNumDocAso": "0",
                "iTipoDocAso": "1",
                "dFecEmiDI": "2023-11-01",
                "dNumComRet": "0",
                "dNumResCF": "0",
                "iTipCons": "0",
                "dNumCons": "0",
                "dNumControl": "0",
            }
        ]
    return document


def calcular_y_generar_factura(transaction, invoice_number):
    invoice = build_exchange_invoice(transaction, invoice_number)
    calculation = calcular_de(invoice)
    results = calculation.get("results") or []
    calculated_de = results[0].get("DE") if results and isinstance(results[0], dict) else None
    if not isinstance(calculated_de, dict):
        raise FacturaSeguraError("calcular_de no devolvió el documento calculado.")
    return generar_de(calculated_de), calculated_de


DOCUMENT_NUMBER_RANGES = {
    "factura": (285, 296),
    "nota_credito": (97, 108),
}


def _reserve_document_number(tipo_documento):
    from .models import FacturaElectronica, SecuenciaDocumento

    try:
        minimo, maximo = DOCUMENT_NUMBER_RANGES[tipo_documento]
    except KeyError as error:
        raise FacturaSeguraError("El tipo de documento fiscal no es válido.") from error

    secuencia = SecuenciaDocumento.objects.select_for_update().get(
        tipo_documento=tipo_documento
    )
    numero = max(secuencia.siguiente_numero, minimo)
    while numero <= maximo:
        numero_formateado = str(numero).zfill(7)
        ocupado = FacturaElectronica.objects.filter(
            tipo_documento=tipo_documento,
            numero_documento=numero_formateado,
        ).exists()
        if not ocupado:
            secuencia.siguiente_numero = numero + 1
            secuencia.save(update_fields=["siguiente_numero"])
            return numero_formateado
        numero += 1

    raise FacturaSeguraError(
        f"Se agotó el rango de numeración para {tipo_documento}."
    )


def _validate_emission_configuration(
    transaction,
    tipo_documento,
    cdc_referenciado,
    motivo_nota="",
):
    settings_name = {
        "factura": "DS_I_TI_DE_FACTURA",
        "nota_credito": "DS_I_TI_DE_NOTA",
    }[tipo_documento]
    for setting_name in (
        settings_name,
        "FS_D_NUM_TIM",
        "FS_D_FE_INI_T",
        "FS_D_EST",
        "FS_D_PUN_EXP",
        "FS_I_T_IMP",
        "FS_D_RUC_EM",
        "FS_DV_EMI",
        "FS_I_TIP_CONT",
        "FS_D_NOM_EMI",
        "FS_D_DIR_EMI",
        "FS_D_NUM_CAS",
        "FS_C_DEP_EMI",
        "FS_D_DES_DEP_EMI",
        "FS_C_CIU_EMI",
        "FS_D_DES_CIU_EMI",
        "FS_D_TEL_EMI",
        "FS_D_EMAIL_E",
        "FS_C_ACT_ECO1",
        "FS_D_DES_ACT_ECO1",
        "FS_C_ACT_ECO2",
        "FS_D_DES_ACT_ECO2",
        "FS_I_IND_PRES",
        "FS_I_AFEC_IVA",
        "FS_D_PROP_IVA",
        "FS_D_TASA_IVA",
    ):
        _required_setting(setting_name)

    tipo_operacion_setting = (
        "FS_I_TIP_TRA_COMPRA"
        if transaction.tipo_operacion == "compra"
        else "FS_I_TIP_TRA_VENTA"
    )
    _required_setting(tipo_operacion_setting)
    _required_setting(
        "FS_I_TI_OPE_B2C"
        if transaction.cliente.tipo_persona == "FISICA"
        else "FS_I_TI_OPE_B2B"
    )
    _required_setting(
        "FS_I_TI_CONT_REC_FISICA"
        if transaction.cliente.tipo_persona == "FISICA"
        else "FS_I_TI_CONT_REC_JURIDICA"
    )
    _required_setting(
        "FS_I_NAT_REC_CONTRIBUYENTE"
        if transaction.cliente.es_contribuyente
        else "FS_I_NAT_REC_NO_CONTRIBUYENTE"
    )
    if tipo_documento == "nota_credito":
        _required_setting("FS_I_MOT_EMI_NOTA")
        if not cdc_referenciado:
            raise FacturaSeguraError(
                "La nota de crédito requiere el CDC de la factura original."
            )
        if not motivo_nota.strip():
            raise FacturaSeguraError("La nota de crédito requiere un motivo.")
    _required_setting("FS_I_FOR_PRO_PA")
    payment_method = transaction.medio_pago
    _required_setting(f"FS_I_DEN_TARJ_{payment_method.marca}")
    if not _recipient_email(transaction.cliente):
        raise FacturaSeguraError(
            "El cliente no tiene un email válido para recibir la factura."
        )


def emitir_documento(
    transaccion,
    tipo_documento="factura",
    cdc_referenciado=None,
    motivo_nota="",
    stripe_refund_id="",
):
    """Issue one electronic document per transaction and document type."""
    from .models import FacturaElectronica

    if tipo_documento not in DOCUMENT_NUMBER_RANGES:
        raise FacturaSeguraError("El tipo de documento fiscal no es válido.")
    if tipo_documento == "nota_credito":
        if not cdc_referenciado:
            raise FacturaSeguraError("La nota de crédito requiere el CDC de la factura original.")
        if not motivo_nota.strip():
            raise FacturaSeguraError("La nota de crédito requiere un motivo.")

    with db_transaction.atomic():
        locked_transaction = (
            Transaccion.objects.select_for_update(of=("self",))
            .select_related("cliente", "cliente__creado_por", "medio_pago", "divisa")
            .get(pk=transaccion.pk)
        )
        _validate_emission_configuration(
            locked_transaction,
            tipo_documento,
            cdc_referenciado,
            motivo_nota,
        )
        factura = FacturaElectronica.objects.filter(
            transaccion=locked_transaction,
            tipo_documento=tipo_documento,
        ).first()
        if factura is not None:
            return factura

        factura = FacturaElectronica.objects.create(
            transaccion=locked_transaction,
            tipo_documento=tipo_documento,
            motivo=motivo_nota.strip()[:500],
            stripe_refund_id=stripe_refund_id,
            numero_documento=_reserve_document_number(tipo_documento),
            estado=FacturaElectronica.ESTADO_EMITIENDO,
        )

    try:
        documento = build_exchange_invoice(
            locked_transaction,
            factura.numero_documento,
            tipo_documento=tipo_documento,
            cdc_referenciado=cdc_referenciado,
            motivo_nota=motivo_nota,
        )
        factura.documento = documento
        factura.save(update_fields=["documento", "fecha_actualizacion"])

        calculo = calcular_de(documento)
        resultados_calculo = calculo.get("results") or []
        documento_calculado = (
            resultados_calculo[0].get("DE")
            if resultados_calculo and isinstance(resultados_calculo[0], dict)
            else None
        )
        if not isinstance(documento_calculado, dict):
            raise FacturaSeguraError(
                "calcular_de no devolvió el documento calculado."
            )
        factura.documento = documento_calculado
        factura.save(update_fields=["documento", "fecha_actualizacion"])

        respuesta = generar_de(documento_calculado)
        resultados = respuesta.get("results") or []
        cdc = resultados[0].get("CDC") if resultados and isinstance(resultados[0], dict) else None
        if not cdc:
            raise FacturaSeguraError("generar_de no devolvió el CDC de la factura.")
        factura.cdc = str(cdc)
        factura.respuesta = respuesta
        factura.estado = FacturaElectronica.ESTADO_EMITIDA
        factura.error = ""
        factura.save(
            update_fields=[
                "cdc",
                "respuesta",
                "estado",
                "error",
                "fecha_actualizacion",
            ]
        )
        return factura
    except Exception as error:
        factura.estado = FacturaElectronica.ESTADO_ERROR
        factura.error = str(error)[:4000]
        factura.save(update_fields=["estado", "error", "fecha_actualizacion"])
        raise


def emitir_factura(transaccion):
    return emitir_documento(transaccion, tipo_documento="factura")


def emitir_nota_credito(
    transaccion,
    cdc_referenciado,
    motivo,
    stripe_refund_id="",
):
    return emitir_documento(
        transaccion,
        tipo_documento="nota_credito",
        cdc_referenciado=cdc_referenciado,
        motivo_nota=motivo,
        stripe_refund_id=stripe_refund_id,
    )


def _headers():
    token = settings.FS_TOKEN
    if not token:
        raise FacturaSeguraConfigurationError("FS_TOKEN no está configurado.")
    return {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authentication-Token": token,
    }


def _parse_json_response(response):
    response.raise_for_status()
    try:
        result = response.json()
    except ValueError as error:
        raise FacturaSeguraError(
            "Factura Segura devolvió una respuesta que no es JSON."
        ) from error

    if not isinstance(result, dict) or not isinstance(result.get("code"), int):
        raise FacturaSeguraError("La respuesta de Factura Segura no tiene un code válido.")
    if result["code"] < 0:
        raise FacturaSeguraAPIError(
            result["code"], result.get("description", "Error de API"), result
        )
    return result


def call_operation(operation, params):
    """Call a Factura Segura POST operation using its standard JSON envelope."""
    payload = {"operation": operation, "params": params}

    response = requests.post(
        settings.FS_API_URL,
        headers=_headers(),
        json=payload,
        timeout=settings.FS_TIMEOUT_SECONDS,
    )
    return _parse_json_response(response)


def calcular_de(de):
    return call_operation("calcular_de", {"DE": de})


def generar_de(de):
    return call_operation("generar_de", {"DE": de})


def get_estado_sifen(cdc, ruc_emisor):
    return call_operation("get_estado_sifen", {"CDC": cdc, "dRucEm": ruc_emisor})


def sol_cancelacion(cdc, ruc_emisor):
    return call_operation("sol_cancelacion", {"CDC": cdc, "dRucEm": ruc_emisor})


def sol_inutilizacion(
    ruc_emisor,
    tipo_documento,
    numero_timbrado,
    establecimiento,
    punto_expedicion,
    numero_documento,
):
    return call_operation(
        "sol_inutilizacion",
        {
            "dRucEm": ruc_emisor,
            "iTiDE": tipo_documento,
            "dNumTim": numero_timbrado,
            "dEst": establecimiento,
            "dPunExp": punto_expedicion,
            "dNumDoc": numero_documento,
        },
    )


def _download_document(operation, ruc_emisor, cdc):
    response = requests.get(
        f"{settings.FS_API_URL.rstrip('/')}/{operation}/"
        f"{quote(str(ruc_emisor), safe='')}/{quote(str(cdc), safe='')}",
        headers=_headers(),
        timeout=settings.FS_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.content


def dwn_kude(ruc_emisor, cdc):
    return _download_document("dwn_kude", ruc_emisor, cdc)


def dwn_xml(ruc_emisor, cdc):
    return _download_document("dwn_xml", ruc_emisor, cdc)