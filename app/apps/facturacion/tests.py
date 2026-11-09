from unittest.mock import Mock, patch
from types import SimpleNamespace
import time

from django.db import transaction
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.divisas.models import Moneda
from apps.payments.models import MedioPago
from apps.stripe.services import refund_transaction
from apps.transacciones.models import Transaccion

from . import services
from .models import FacturaElectronica, SecuenciaDocumento


@override_settings(
    FS_TOKEN="test-token",
    FS_API_URL="https://api.facturasegura.test/misife00/v1/esi",
    FS_TIMEOUT_SECONDS=5,
)
class FacturaSeguraServiceTests(SimpleTestCase):
    def respuesta_api(self, code=0, **extra):
        response = Mock()
        response.json.return_value = {"code": code, "description": "OK", **extra}
        return response

    @patch("apps.facturacion.services.requests.post")
    def test_post_envia_envelope_y_token_en_header(self, post):
        post.return_value = self.respuesta_api(results=[])

        result = services.calcular_de({"iTiDE": "1"})

        self.assertEqual(result["code"], 0)
        post.assert_called_once_with(
            "https://api.facturasegura.test/misife00/v1/esi",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authentication-Token": "test-token",
            },
            json={"operation": "calcular_de", "params": {"DE": {"iTiDE": "1"}}},
            timeout=5,
        )

    @patch("builtins.print")
    @patch("apps.facturacion.services.requests.post")
    def test_prints_copyable_curl_for_calculate_and_generate_without_token(
        self,
        post,
        print_output,
    ):
        post.return_value = self.respuesta_api(results=[])

        services.calcular_de({"iTiDE": "1"})
        services.generar_de({"iTiDE": "1"})

        output = "\n".join(call.args[0] for call in print_output.call_args_list)
        self.assertIn("# Factura Segura: calcular_de", output)
        self.assertIn("# Factura Segura: generar_de", output)
        self.assertIn('--header "Authentication-Token: ${FS_TOKEN}"', output)
        self.assertIn("\\\n  --header", output)
        self.assertNotIn("test-token", output)
        self.assertNotIn("+  --header", output)

    @patch("apps.facturacion.services.requests.post")
    def test_funciones_envian_parametros_documentados(self, post):
        post.return_value = self.respuesta_api(results=[])

        services.generar_de({"iTiDE": "1"})
        services.get_estado_sifen("cdc-1", "80002247")
        services.sol_cancelacion("cdc-1", "80002247")
        services.sol_inutilizacion("80002247", "1", "12345678", "001", "002", "3")

        self.assertEqual(
            [call.kwargs["json"] for call in post.call_args_list],
            [
                {"operation": "generar_de", "params": {"DE": {"iTiDE": "1"}}},
                {
                    "operation": "get_estado_sifen",
                    "params": {"CDC": "cdc-1", "dRucEm": "80002247"},
                },
                {
                    "operation": "sol_cancelacion",
                    "params": {"CDC": "cdc-1", "dRucEm": "80002247"},
                },
                {
                    "operation": "sol_inutilizacion",
                    "params": {
                        "dRucEm": "80002247",
                        "iTiDE": "1",
                        "dNumTim": "12345678",
                        "dEst": "001",
                        "dPunExp": "002",
                        "dNumDoc": "3",
                    },
                },
            ],
        )

    @patch("apps.facturacion.services.requests.post")
    def test_error_de_api_negativo_se_expone_como_excepcion(self, post):
        post.return_value = self.respuesta_api(-10001, description="DE inválido")

        with self.assertRaises(services.FacturaSeguraAPIError) as error:
            services.generar_de({})

        self.assertEqual(error.exception.code, -10001)
        self.assertEqual(error.exception.response["description"], "DE inválido")

    @patch("apps.facturacion.services.generar_de")
    @patch("apps.facturacion.services.calcular_de")
    @patch("apps.facturacion.services.build_exchange_invoice")
    def test_calculated_de_is_forwarded_unchanged_to_generate(
        self,
        build_invoice,
        calculate,
        generate,
    ):
        invoice = {"iTiDE": "1", "dNumDoc": "0000285"}
        calculated_invoice = {**invoice, "dTotGralOpe": "71000"}
        build_invoice.return_value = invoice
        calculate.return_value = {
            "code": 0,
            "results": [{"DE": calculated_invoice}],
        }
        generate.return_value = {
            "code": 0,
            "results": [{"CDC": "1" * 44}],
        }
        transaction = object()

        response, result = services.calcular_y_generar_factura(
            transaction,
            "0000285",
        )

        build_invoice.assert_called_once_with(transaction, "0000285")
        calculate.assert_called_once_with(invoice)
        generate.assert_called_once_with(calculated_invoice)
        self.assertEqual(result, calculated_invoice)
        self.assertEqual(response["results"][0]["CDC"], "1" * 44)

    @patch("apps.facturacion.services.generar_de")
    @patch("apps.facturacion.services.calcular_de")
    @patch("apps.facturacion.services.build_exchange_invoice")
    def test_calculation_without_document_does_not_call_generate(
        self,
        build_invoice,
        calculate,
        generate,
    ):
        build_invoice.return_value = {"iTiDE": "1"}
        calculate.return_value = {"code": 0, "results": []}

        with self.assertRaisesRegex(
            services.FacturaSeguraError,
            "documento calculado",
        ):
            services.calcular_y_generar_factura(object(), "0000285")
        generate.assert_not_called()

    @patch("apps.facturacion.services.requests.get")
    def test_descargas_get_incluyen_token_y_retorna_bytes(self, get):
        get.return_value = Mock(content=b"documento")

        result = services.dwn_kude("80002247", "cdc/uno")

        self.assertEqual(result, b"documento")
        get.assert_called_once_with(
            "https://api.facturasegura.test/misife00/v1/esi/dwn_kude/"
            "80002247/cdc%2Funo",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authentication-Token": "test-token",
            },
            timeout=5,
        )

    @override_settings(FS_TOKEN="")
    @patch("apps.facturacion.services.requests.post")
    def test_requiere_token_configurado(self, post):
        with self.assertRaises(services.FacturaSeguraConfigurationError):
            services.generar_de({})
        post.assert_not_called()


@override_settings(
    FS_D_NUM_TIM="80002247",
    FS_D_FE_INI_T="2025-01-01",
    FS_D_EST="001",
    FS_D_PUN_EXP="001",
    FS_I_TIP_TRA_COMPRA="2",
    FS_I_TIP_TRA_VENTA="1",
    FS_I_T_IMP="1",
    FS_D_RUC_EM="80002247",
    FS_DV_EMI="5",
    FS_I_TIP_CONT="2",
    FS_D_NOM_EMI="Casa de cambio de prueba",
    FS_D_DIR_EMI="Calle 1",
    FS_D_NUM_CAS="1",
    FS_C_DEP_EMI="1",
    FS_D_DES_DEP_EMI="CAPITAL",
    FS_C_CIU_EMI="1",
    FS_D_DES_CIU_EMI="ASUNCION",
    FS_D_TEL_EMI="021000000",
    FS_D_EMAIL_E="emisor@example.test",
    FS_C_ACT_ECO1="66120",
    FS_D_DES_ACT_ECO1="Cambio de divisas",
    FS_C_ACT_ECO2="66120",
    FS_D_DES_ACT_ECO2="Servicios financieros",
    FS_I_NAT_REC_CONTRIBUYENTE="1",
    FS_I_NAT_REC_NO_CONTRIBUYENTE="2",
    FS_I_TI_CONT_REC_FISICA="1",
    FS_I_TI_CONT_REC_JURIDICA="2",
    FS_I_TI_OPE_B2B="2",
    FS_I_TI_OPE_B2C="1",
    DS_I_TI_DE_FACTURA="1",
    DS_I_TI_DE_NOTA="5",
    FS_I_MOT_EMI_NOTA="1",
    FS_I_IND_PRES="1",
    FS_I_DEN_TARJ_VISA="1",
    FS_I_FOR_PRO_PA="1",
    FS_I_AFEC_IVA="3",
    FS_D_PROP_IVA="0",
    FS_D_TASA_IVA="0",
)
class ExchangeInvoicePayloadTests(SimpleTestCase):
    def test_builds_pyg_invoice_with_exchange_detail_and_card_payment(self):
        client = SimpleNamespace(
            email="cliente@example.test",
            documento="12345678",
            tipo_persona="FISICA",
            es_contribuyente=False,
            nombre_razon_social="Cliente de prueba",
            creado_por=None,
        )
        medio_pago = SimpleNamespace(
            tipo="CREDITO",
            marca="VISA",
            ultimos_cuatro="4242",
        )
        transaction = SimpleNamespace(
            estado="pagada",
            medio_pago_id=3,
            cliente=client,
            medio_pago=medio_pago,
            tipo_operacion="compra",
            divisa=SimpleNamespace(codigo="USD"),
            cantidad_divisa="10.00",
            monto="71000.00",
            referencia="GE-TEST-1",
            pk=12,
        )

        document = services.build_exchange_invoice(transaction, 23)

        self.assertEqual(document["dNumDoc"], "0000023")
        self.assertEqual(document["CDC"], "0")
        self.assertEqual(document["dCodSeg"], "0")
        self.assertEqual(document["dDVId"], "0")
        self.assertEqual(document["dSisFact"], "1")
        self.assertEqual(document["iTiDE"], "1")
        self.assertEqual(document["iTipTra"], "2")
        self.assertEqual(document["iTiOpe"], "1")
        self.assertEqual(document["iNatRec"], "2")
        self.assertEqual(document["iTiContRec"], "1")
        self.assertEqual(document["cMoneOpe"], "PYG")
        self.assertEqual(document["dTiCam"], "1")
        self.assertEqual(document["dNumIDRec"], "12345678")
        self.assertEqual(document["dEmailRec"], "cliente@example.test")
        self.assertEqual(document["gPaConEIni"][0]["dMonTiPag"], "71000")
        self.assertEqual(document["gPaConEIni"][0]["iTiPago"], "3")
        self.assertEqual(document["gPaConEIni"][0]["iForProPa"], "1")
        self.assertIn("COMPRA de 10 USD", document["gCamItem"][0]["dDesProSer"])
        self.assertIn("7100 PYG por USD", document["gCamItem"][0]["dDesProSer"])

    def test_rejects_transaction_without_email_for_invoice_recipient(self):
        client = SimpleNamespace(
            email="",
            documento="12345678",
            tipo_persona="FISICA",
            es_contribuyente=False,
            nombre_razon_social="Cliente de prueba",
            creado_por=None,
        )
        transaction = SimpleNamespace(
            estado="pagada",
            medio_pago_id=3,
            cliente=client,
            medio_pago=SimpleNamespace(
                tipo="CREDITO",
                marca="VISA",
                ultimos_cuatro="4242",
            ),
            tipo_operacion="compra",
            divisa=SimpleNamespace(codigo="USD"),
            cantidad_divisa="10.00",
            monto="71000.00",
            referencia="GE-TEST-2",
            pk=13,
        )

        with self.assertRaisesRegex(services.FacturaSeguraError, "email"):
            services.build_exchange_invoice(transaction, 24)

    def test_selects_sale_b2b_and_contributor_codes(self):
        client = SimpleNamespace(
            email="empresa@example.test",
            documento="800022475",
            tipo_persona="JURIDICA",
            es_contribuyente=True,
            nombre_razon_social="Empresa de prueba",
            creado_por=None,
        )
        transaction = SimpleNamespace(
            estado="pagada",
            medio_pago_id=3,
            cliente=client,
            medio_pago=SimpleNamespace(
                tipo="DEBITO",
                marca="VISA",
                ultimos_cuatro="4242",
            ),
            tipo_operacion="venta",
            divisa=SimpleNamespace(codigo="USD"),
            cantidad_divisa="10.00",
            monto="70000.00",
            referencia="GE-TEST-3",
            pk=14,
        )

        document = services.build_exchange_invoice(transaction, 25)

        self.assertEqual(document["iTipTra"], "1")
        self.assertEqual(document["iTiOpe"], "2")
        self.assertEqual(document["iNatRec"], "1")
        self.assertEqual(document["iTiContRec"], "2")
        self.assertEqual(document["dRucRec"], "80002247")
        self.assertEqual(document["dDVRec"], "5")
        self.assertEqual(document["iTipIDRec"], "0")
        self.assertEqual(document["gPaConEIni"][0]["iTiPago"], "4")

    @override_settings(FS_I_FOR_PRO_PA="")
    def test_missing_card_processing_code_fails_with_setting_name(self):
        client = SimpleNamespace(
            email="cliente@example.test",
            documento="12345678",
            tipo_persona="FISICA",
            es_contribuyente=False,
            nombre_razon_social="Cliente de prueba",
            creado_por=None,
        )
        transaction = SimpleNamespace(
            estado="pagada",
            medio_pago_id=3,
            cliente=client,
            medio_pago=SimpleNamespace(
                tipo="CREDITO",
                marca="VISA",
                ultimos_cuatro="4242",
            ),
            tipo_operacion="compra",
            divisa=SimpleNamespace(codigo="USD"),
            cantidad_divisa="10.00",
            monto="71000.00",
            referencia="GE-TEST-CONFIG",
            pk=16,
        )

        with self.assertRaisesRegex(
            services.FacturaSeguraConfigurationError,
            "FS_I_FOR_PRO_PA",
        ):
            services.build_exchange_invoice(transaction, 27)

    def test_note_credit_requires_original_cdc_and_uses_configured_code(self):
        client = SimpleNamespace(
            email="cliente@example.test",
            documento="12345678",
            tipo_persona="FISICA",
            es_contribuyente=False,
            nombre_razon_social="Cliente de prueba",
            creado_por=None,
        )
        transaction = SimpleNamespace(
            estado="pagada",
            medio_pago_id=3,
            cliente=client,
            medio_pago=SimpleNamespace(
                tipo="CREDITO",
                marca="VISA",
                ultimos_cuatro="4242",
            ),
            tipo_operacion="compra",
            divisa=SimpleNamespace(codigo="USD"),
            cantidad_divisa="10.00",
            monto="71000.00",
            referencia="GE-TEST-4",
            pk=15,
        )

        with self.assertRaisesRegex(services.FacturaSeguraError, "CDC"):
            services.build_exchange_invoice(
                transaction,
                26,
                tipo_documento="nota_credito",
            )
        document = services.build_exchange_invoice(
            transaction,
            26,
            tipo_documento="nota_credito",
            cdc_referenciado="0" * 44,
            motivo_nota="Reembolso solicitado por el cliente",
        )
        self.assertEqual(document["iTiDE"], "5")
        self.assertEqual(document["dInfAdic"], "Reembolso solicitado por el cliente")
        self.assertEqual(document["gCamDEAsoc"][0]["dCdCDERef"], "0" * 44)


class DocumentNumberSequenceTests(TestCase):
    def test_invoice_numbers_start_at_285_and_advance_independently(self):
        with transaction.atomic():
            first_invoice = services._reserve_document_number("factura")
            first_credit_note = services._reserve_document_number("nota_credito")
            second_invoice = services._reserve_document_number("factura")

        self.assertEqual(first_invoice, "0000285")
        self.assertEqual(second_invoice, "0000286")
        self.assertEqual(first_credit_note, "0000097")

    def test_sequences_stop_at_their_configured_upper_bounds(self):
        SecuenciaDocumento.objects.filter(tipo_documento="factura").update(
            siguiente_numero=297
        )
        SecuenciaDocumento.objects.filter(tipo_documento="nota_credito").update(
            siguiente_numero=109
        )

        with transaction.atomic():
            with self.assertRaisesRegex(services.FacturaSeguraError, "Se agotó"):
                services._reserve_document_number("factura")
        with transaction.atomic():
            with self.assertRaisesRegex(services.FacturaSeguraError, "Se agotó"):
                services._reserve_document_number("nota_credito")

    def test_upper_bounds_are_included(self):
        SecuenciaDocumento.objects.filter(tipo_documento="factura").update(
            siguiente_numero=296
        )
        SecuenciaDocumento.objects.filter(tipo_documento="nota_credito").update(
            siguiente_numero=108
        )

        with transaction.atomic():
            last_invoice = services._reserve_document_number("factura")
            last_credit_note = services._reserve_document_number("nota_credito")

        self.assertEqual(last_invoice, "0000296")
        self.assertEqual(last_credit_note, "0000108")

    def test_unknown_document_type_has_no_sequence(self):
        with self.assertRaisesRegex(services.FacturaSeguraError, "tipo de documento"):
            services._reserve_document_number("otro")


class IssueInvoiceLockingTests(TestCase):
    def test_issue_invoice_locks_only_transaction_and_reaches_api_operations(self):
        user = get_user_model().objects.create_user(
            username="invoice-lock-test",
            password="test-password",
        )
        client = Cliente.objects.create(
            nombre_razon_social="Cliente de prueba",
            documento="12345678",
            creado_por=user,
        )
        medio_pago = MedioPago.objects.create(
            cliente=client,
            tipo="CREDITO",
            alias="Tarjeta de prueba",
            titular="Cliente de prueba",
            marca="VISA",
            ultimos_cuatro="4242",
            mes_vencimiento=12,
            anio_vencimiento=2099,
        )
        pyg = Moneda.objects.get(codigo="PYG")
        usd = Moneda.objects.create(
            codigo="USD",
            nombre="Dólar estadounidense",
            simbolo="$",
        )
        transaccion = Transaccion.objects.create(
            cliente=client,
            medio_pago=medio_pago,
            monto="71000.00",
            cantidad_divisa="10.00",
            divisa=usd,
            tipo_operacion="compra",
            moneda=pyg,
            estado=Transaccion.ESTADO_PAGADA,
            referencia="GE-LOCK-TEST",
        )
        documento_calculado = {"iTiDE": "1", "dTotGralOpe": "71000"}

        with (
            patch("apps.facturacion.services._validate_emission_configuration"),
            patch(
                "apps.facturacion.services.build_exchange_invoice",
                return_value={"iTiDE": "1"},
            ),
            patch(
                "apps.facturacion.services.calcular_de",
                return_value={"code": 0, "results": [{"DE": documento_calculado}]},
            ) as calcular,
            patch(
                "apps.facturacion.services.generar_de",
                return_value={"code": 0, "results": [{"CDC": "1" * 44}]},
            ) as generar,
        ):
            invoice = services.emitir_factura(transaccion)

        self.assertEqual(invoice.estado, FacturaElectronica.ESTADO_EMITIDA)
        self.assertEqual(invoice.cdc, "1" * 44)
        calcular.assert_called_once_with({"iTiDE": "1"})
        generar.assert_called_once_with(documento_calculado)


class ElectronicDocumentDownloadTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="invoice-download-test",
            password="test-password",
        )
        self.client_record = Cliente.objects.create(
            nombre_razon_social="Cliente de descarga",
            documento="12345678",
            activo=True,
            creado_por=self.user,
        )
        self.payment_method = MedioPago.objects.create(
            cliente=self.client_record,
            tipo="CREDITO",
            alias="Tarjeta de prueba",
            titular="Cliente de descarga",
            marca="VISA",
            ultimos_cuatro="4242",
            mes_vencimiento=12,
            anio_vencimiento=2099,
        )
        self.pyg = Moneda.objects.get(codigo="PYG")
        self.usd = Moneda.objects.create(
            codigo="USD",
            nombre="Dólar estadounidense",
            simbolo="$",
        )
        self.transaction = Transaccion.objects.create(
            cliente=self.client_record,
            medio_pago=self.payment_method,
            monto="71000.00",
            cantidad_divisa="10.00",
            divisa=self.usd,
            tipo_operacion="compra",
            moneda=self.pyg,
            estado=Transaccion.ESTADO_PAGADA,
            referencia="GE-DOWNLOAD-TEST",
        )
        self.invoice = FacturaElectronica.objects.create(
            transaccion=self.transaction,
            tipo_documento=FacturaElectronica.TIPO_FACTURA,
            numero_documento="0000285",
            cdc="1" * 44,
            estado=FacturaElectronica.ESTADO_EMITIDA,
        )
        self.client.force_login(self.user)
        session = self.client.session
        session["active_client_id"] = self.client_record.pk
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.services.dwn_kude")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_approved_invoice_can_download_kude(self, get_state, download):
        get_state.return_value = {
            "code": 0,
            "results": [{"estado_sifen": "Aprobado", "estado_can": ""}],
        }
        download.return_value = b"%PDF-test"

        response = self.client.get(
            reverse("facturacion:descargar", args=(self.invoice.pk, "kude"))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"%PDF-test")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment;", response["Content-Disposition"])
        get_state.assert_called_once_with("1" * 44, "80002247")
        download.assert_called_once_with("80002247", "1" * 44)

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.services.dwn_xml")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_approved_with_observation_can_download_xml(self, get_state, download):
        get_state.return_value = {
            "code": 0,
            "results": [
                {"estado_sifen": "Aprobado con observación", "estado_can": ""}
            ],
        }
        download.return_value = b"<xml/>"

        response = self.client.get(
            reverse("facturacion:descargar", args=(self.invoice.pk, "xml"))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"<xml/>")
        self.assertEqual(response["Content-Type"], "application/xml")
        download.assert_called_once_with("80002247", "1" * 44)

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.services.dwn_kude")
    @patch("apps.facturacion.views.services.dwn_xml")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_credit_note_can_download_kude_and_xml(
        self,
        get_state,
        download_xml,
        download_kude,
    ):
        credit_note = FacturaElectronica.objects.create(
            transaccion=self.transaction,
            tipo_documento=FacturaElectronica.TIPO_NOTA_CREDITO,
            numero_documento="0000097",
            cdc="2" * 44,
            estado=FacturaElectronica.ESTADO_EMITIDA,
        )
        get_state.return_value = {
            "code": 0,
            "results": [{"estado_sifen": "Aprobado", "estado_can": ""}],
        }
        download_kude.return_value = b"%PDF-credit-note"
        download_xml.return_value = b"<credit-note/>"

        kude_response = self.client.get(
            reverse("facturacion:descargar", args=(credit_note.pk, "kude"))
        )
        xml_response = self.client.get(
            reverse("facturacion:descargar", args=(credit_note.pk, "xml"))
        )

        self.assertEqual(kude_response.status_code, 200)
        self.assertEqual(kude_response.content, b"%PDF-credit-note")
        self.assertEqual(xml_response.status_code, 200)
        self.assertEqual(xml_response.content, b"<credit-note/>")
        self.assertEqual(
            [call.args[0] for call in get_state.call_args_list],
            ["2" * 44, "2" * 44],
        )
        download_kude.assert_called_once_with("80002247", "2" * 44)
        download_xml.assert_called_once_with("80002247", "2" * 44)

    def test_history_shows_download_links_for_emitted_credit_note(self):
        credit_note = FacturaElectronica.objects.create(
            transaccion=self.transaction,
            tipo_documento=FacturaElectronica.TIPO_NOTA_CREDITO,
            numero_documento="0000097",
            cdc="2" * 44,
            estado=FacturaElectronica.ESTADO_EMITIDA,
        )

        response = self.client.get(reverse("transacciones:historial"))

        self.assertContains(
            response,
            reverse("facturacion:descargar", args=(credit_note.pk, "kude")),
        )
        self.assertContains(
            response,
            reverse("facturacion:descargar", args=(credit_note.pk, "xml")),
        )
        self.assertContains(response, "Nota de crédito 0000097")

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.services.dwn_xml")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_unapproved_invoice_cannot_download_xml(self, get_state, download):
        get_state.return_value = {
            "code": 0,
            "results": [{"estado_sifen": "ENVIADO_A_SIFEN", "estado_can": ""}],
        }

        response = self.client.get(
            reverse("facturacion:descargar", args=(self.invoice.pk, "xml")),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.redirect_chain,
            [(reverse("transacciones:historial"), 302)],
        )
        self.assertContains(response, "Factura todavía no disponible")
        self.assertContains(response, "Transacción GE-DOWNLOAD-TEST")
        self.assertContains(response, "SIFEN todavía no la aprobó")
        reload_response = self.client.get(reverse("transacciones:historial"))
        self.assertNotContains(reload_response, "Factura todavía no disponible")
        download.assert_not_called()

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.services.dwn_xml")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_approved_cancellation_blocks_download(self, get_state, download):
        get_state.return_value = {
            "code": 0,
            "results": [
                {"estado_sifen": "Aprobado", "estado_can": "Aprobado"}
            ],
        }

        response = self.client.get(
            reverse("facturacion:descargar", args=(self.invoice.pk, "xml")),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Factura todavía no disponible")
        self.assertContains(response, "Transacción GE-DOWNLOAD-TEST")
        self.assertContains(response, "fue cancelada o inutilizada")
        download.assert_not_called()


class CreditNoteRefundRequestTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="credit-note-refund-test",
            password="test-password",
        )
        self.client_record = Cliente.objects.create(
            nombre_razon_social="Cliente de reembolso",
            documento="12345678",
            activo=True,
            creado_por=self.user,
        )
        self.payment_method = MedioPago.objects.create(
            cliente=self.client_record,
            tipo="CREDITO",
            alias="Tarjeta de prueba",
            titular="Cliente",
            marca="VISA",
            ultimos_cuatro="4242",
            mes_vencimiento=12,
            anio_vencimiento=2099,
        )
        self.pyg = Moneda.objects.get(codigo="PYG")
        self.usd = Moneda.objects.create(
            codigo="USD",
            nombre="Dólar estadounidense",
            simbolo="$",
        )
        self.transaction = Transaccion.objects.create(
            cliente=self.client_record,
            medio_pago=self.payment_method,
            monto="71000.00",
            cantidad_divisa="10.00",
            divisa=self.usd,
            tipo_operacion="compra",
            moneda=self.pyg,
            estado=Transaccion.ESTADO_PAGADA,
            referencia="GE-REFUND-TEST",
            fecha_finalizacion=timezone.now(),
            stripe_payment_intent_id="pi_refund_test",
        )
        self.invoice = FacturaElectronica.objects.create(
            transaccion=self.transaction,
            tipo_documento=FacturaElectronica.TIPO_FACTURA,
            numero_documento="0000285",
            cdc="2" * 44,
            estado=FacturaElectronica.ESTADO_EMITIDA,
        )
        self.client.force_login(self.user)
        session = self.client.session
        session["active_client_id"] = self.client_record.pk
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.services.emitir_nota_credito")
    @patch("apps.facturacion.views.refund_transaction")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_refund_and_note_are_requested_with_reason(
        self,
        get_state,
        refund,
        issue_credit_note,
    ):
        get_state.return_value = {
            "code": 0,
            "results": [{"estado_sifen": "Aprobado", "estado_can": ""}],
        }
        refund.return_value = SimpleNamespace(status="succeeded", id="re_test_1")
        issue_credit_note.return_value = SimpleNamespace(
            numero_documento="0000097",
            cdc="3" * 44,
            save=Mock(),
        )

        response = self.client.post(
            reverse(
                "facturacion:solicitar_nota_credito",
                args=(self.transaction.pk,),
            ),
            {"motivo": "Cliente desistió de la operación"},
        )

        self.assertRedirects(response, reverse("transacciones:historial"))
        get_state.assert_called_once_with("2" * 44, "80002247")
        issue_credit_note.assert_called_once_with(
            self.transaction,
            "2" * 44,
            "Cliente desistió de la operación",
        )
        refund.assert_called_once_with(
            self.transaction,
            "Cliente desistió de la operación",
        )
        self.assertEqual(issue_credit_note.return_value.stripe_refund_id, "re_test_1")
        issue_credit_note.return_value.save.assert_called_once_with(
            update_fields=["stripe_refund_id", "fecha_actualizacion"]
        )

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("builtins.print")
    @patch("apps.facturacion.views.refund_transaction")
    @patch("apps.facturacion.views.services.emitir_nota_credito")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_factura_segura_rejection_prevents_stripe_refund_and_prints_response(
        self,
        get_state,
        issue_credit_note,
        refund,
        print_output,
    ):
        get_state.return_value = {
            "code": 0,
            "results": [{"estado_sifen": "Aprobado", "estado_can": ""}],
        }
        issue_credit_note.side_effect = services.FacturaSeguraAPIError(
            -10001,
            "DE inválido",
            {"code": -10001, "description": "DE inválido"},
        )

        response = self.client.post(
            reverse("facturacion:solicitar_nota_credito", args=(self.transaction.pk,)),
            {"motivo": "Cliente desistió de la operación"},
        )

        self.assertRedirects(response, reverse("transacciones:historial"))
        refund.assert_not_called()
        print_output.assert_called_once_with(
            "Respuesta de rechazo de Factura Segura: "
            "{'code': -10001, 'description': 'DE inválido'}",
            flush=True,
        )

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.services.sol_cancelacion")
    @patch("apps.facturacion.views.refund_transaction")
    @patch("apps.facturacion.views.services.emitir_nota_credito")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_stripe_rejection_requests_credit_note_cancellation(
        self,
        get_state,
        issue_credit_note,
        refund,
        cancel_note,
    ):
        get_state.return_value = {
            "code": 0,
            "results": [{"estado_sifen": "Aprobado", "estado_can": ""}],
        }
        issue_credit_note.return_value = SimpleNamespace(
            numero_documento="0000097",
            cdc="3" * 44,
            save=Mock(),
        )
        refund.return_value = SimpleNamespace(status="failed", id="re_failed")

        response = self.client.post(
            reverse("facturacion:solicitar_nota_credito", args=(self.transaction.pk,)),
            {"motivo": "Cliente desistió de la operación"},
        )

        self.assertRedirects(response, reverse("transacciones:historial"))
        cancel_note.assert_called_once_with("3" * 44, "80002247")

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.refund_transaction")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_rejects_refund_after_three_days_before_stripe_call(
        self,
        get_state,
        refund,
    ):
        self.transaction.fecha_finalizacion = timezone.now() - timezone.timedelta(days=3, seconds=1)
        self.transaction.save(update_fields=["fecha_finalizacion"])

        response = self.client.post(
            reverse(
                "facturacion:solicitar_nota_credito",
                args=(self.transaction.pk,),
            ),
            {"motivo": "Cliente desistió de la operación"},
        )

        self.assertRedirects(response, reverse("transacciones:historial"))
        get_state.assert_not_called()
        refund.assert_not_called()

    @override_settings(FS_D_RUC_EM="80002247")
    @patch("apps.facturacion.views.refund_transaction")
    @patch("apps.facturacion.views.services.get_estado_sifen")
    def test_unapproved_original_invoice_is_not_refunded(self, get_state, refund):
        get_state.return_value = {
            "code": 0,
            "results": [{"estado_sifen": "ENVIADO_A_SIFEN", "estado_can": ""}],
        }

        response = self.client.post(
            reverse(
                "facturacion:solicitar_nota_credito",
                args=(self.transaction.pk,),
            ),
            {"motivo": "Cliente desistió de la operación"},
        )

        self.assertRedirects(response, reverse("transacciones:historial"))
        refund.assert_not_called()

    @patch("apps.facturacion.views.refund_transaction")
    def test_requires_a_reason(self, refund):
        response = self.client.post(
            reverse(
                "facturacion:solicitar_nota_credito",
                args=(self.transaction.pk,),
            ),
            {"motivo": "  "},
        )

        self.assertRedirects(response, reverse("transacciones:historial"))
        refund.assert_not_called()

    def test_history_shows_reason_form_for_eligible_payment(self):
        response = self.client.get(reverse("transacciones:historial"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reembolso y nota de crédito")
        self.assertContains(response, f'action="{reverse("facturacion:solicitar_nota_credito", args=(self.transaction.pk,))}"')
        self.assertContains(response, 'name="motivo"')
        self.assertRegex(
            response.content.decode(),
            r'<form[^>]*action="[^"]*nota-credito/[^"]*"[^>]*>\s*<input[^>]*name="csrfmiddlewaretoken"[^>]*value="[^" ]+"',
        )

    def test_history_hides_reason_form_after_three_day_window(self):
        self.transaction.fecha_finalizacion = timezone.now() - timezone.timedelta(days=3, seconds=1)
        self.transaction.save(update_fields=["fecha_finalizacion"])

        response = self.client.get(reverse("transacciones:historial"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Reembolso y nota de crédito")

    def test_history_explains_missing_stripe_payment_intent(self):
        self.transaction.stripe_payment_intent_id = ""
        self.transaction.save(update_fields=["stripe_payment_intent_id"])

        response = self.client.get(reverse("transacciones:historial"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Reembolso y nota de crédito")

    def test_history_explains_when_original_invoice_is_missing(self):
        self.invoice.delete()

        response = self.client.get(reverse("transacciones:historial"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Reembolso y nota de crédito")

    @patch("apps.stripe.services.stripe.Refund.retrieve")
    @patch("apps.stripe.services.stripe.Refund.create")
    def test_stripe_refund_is_idempotent_and_reason_cannot_change(
        self,
        create_refund,
        retrieve_refund,
    ):
        create_refund.return_value = SimpleNamespace(
            id="re_idempotent_test",
            status="pending",
        )

        first_result = refund_transaction(self.transaction, "Motivo original")

        self.assertEqual(first_result.id, "re_idempotent_test")
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.stripe_refund_id, "re_idempotent_test")
        self.assertEqual(self.transaction.stripe_refund_reason, "Motivo original")
        self.assertEqual(
            create_refund.call_args.kwargs["idempotency_key"],
            f"refund-credit-note:{self.transaction.identificador}",
        )

        retrieve_refund.return_value = SimpleNamespace(
            id="re_idempotent_test",
            status="succeeded",
        )
        second_result = refund_transaction(self.transaction, "Motivo original")
        self.assertEqual(second_result.status, "succeeded")
        retrieve_refund.assert_called_once_with("re_idempotent_test")
        create_refund.assert_called_once()

        with self.assertRaisesRegex(ValueError, "no se puede cambiar"):
            refund_transaction(self.transaction, "Otro motivo")
