from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.divisas.models import Moneda, TasaCambio
from apps.payments.models import ClienteStripeCustomer, MedioPago

from .models import Transaccion


class TransaccionModelTest(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="transaccion_test",
            password="password123",
        )
        self.cliente = Cliente.objects.create(
            nombre_razon_social="Cliente de prueba",
            documento="transaccion-123",
            creado_por=usuario,
        )
        self.medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            tipo="DEBITO",
            alias="Tarjeta principal",
            titular="Cliente Test",
            marca="VISA",
            ultimos_cuatro="4242",
            mes_vencimiento=12,
            anio_vencimiento=2099,
        )
        self.moneda = Moneda.objects.create(
            codigo="USD",
            nombre="Dólar estadounidense",
            simbolo="$",
        )

    def crear_transaccion(self, **kwargs):
        datos = {
            "cliente": self.cliente,
            "medio_pago": self.medio_pago,
            "monto": Decimal("125.50"),
            "moneda": self.moneda,
            "referencia": "TRX-0001",
        }
        datos.update(kwargs)
        return Transaccion.objects.create(**datos)

    def test_crea_transaccion_pendiente(self):
        transaccion = self.crear_transaccion()

        self.assertEqual(transaccion.estado, Transaccion.ESTADO_PENDIENTE)
        self.assertEqual(str(transaccion), "TRX-0001 - 125.50 USD")

    def test_guarda_datos_de_operacion_para_el_historial(self):
        transaccion = self.crear_transaccion(
            cantidad_divisa=Decimal("10.00"),
            divisa=self.moneda,
            tipo_operacion=Transaccion.TIPO_COMPRA,
        )

        self.assertEqual(transaccion.cantidad_divisa, Decimal("10.00"))
        self.assertEqual(transaccion.divisa, self.moneda)
        self.assertEqual(transaccion.get_tipo_operacion_display(), "Compra")

    def test_acepta_todos_los_estados_definidos(self):
        for indice, estado in enumerate(
            dict(Transaccion.ESTADO_CHOICES), start=1
        ):
            transaccion = self.crear_transaccion(
                referencia=f"TRX-000{indice}",
                estado=estado,
            )

            self.assertEqual(transaccion.estado, estado)

    def test_protege_cliente_medio_pago_y_moneda(self):
        self.crear_transaccion()

        with self.assertRaises(ProtectedError):
            self.cliente.delete()
        with self.assertRaises(ProtectedError):
            self.medio_pago.delete()
        with self.assertRaises(ProtectedError):
            self.moneda.delete()


class TransaccionLifecycleTest(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="transaccion_flujo",
            password="password123",
        )
        self.cliente = Cliente.objects.create(
            nombre_razon_social="Cliente de flujo",
            documento="transaccion-flujo-123",
            creado_por=usuario,
            activo=True,
        )
        self.medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            stripe_payment_method_id="pm_transaccion_test",
            tipo="DEBITO",
            alias="Tarjeta principal",
            titular="Cliente Test",
            marca="VISA",
            ultimos_cuatro="4242",
            mes_vencimiento=12,
            anio_vencimiento=2099,
        )
        ClienteStripeCustomer.objects.create(
            cliente=self.cliente,
            stripe_customer_id="cus_transaccion_test",
        )
        self.pyg = Moneda.objects.get(codigo="PYG")
        self.usd = Moneda.objects.create(
            codigo="USD",
            nombre="Dólar estadounidense",
            simbolo="$",
        )
        TasaCambio.objects.create(
            moneda=self.usd,
            tasa_compra=7000,
            tasa_venta=7100,
            usuario_modificador=usuario,
        )
        self.client.force_login(usuario)

    @patch("apps.stripe.services.stripe.PaymentIntent.create")
    def test_calculo_no_guarda_hasta_efectuar_y_se_guarda_como_pagada(
        self, crear_intento
    ):
        crear_intento.return_value = Mock(
            id="pi_transaccion_test",
            status="succeeded",
            latest_charge=Mock(receipt_url="https://stripe.test/receipt"),
        )
        response_calculo = self.client.post(
            reverse("home"),
            {"operation": "compra", "currency": "USD", "amount": "10"},
        )

        self.assertEqual(response_calculo.status_code, 200)
        self.assertFalse(Transaccion.objects.exists())
        self.assertContains(response_calculo, 'value="efectuar"')
        self.assertContains(response_calculo, 'value="guardar_pendiente"')

        response_pago = self.client.post(
            reverse("transacciones:crear"),
            {
                "operation": "compra",
                "amount": "10",
                "currency": "USD",
                "quoted_rate": "7100",
                "medio_pago": self.medio_pago.pk,
                "accion": "efectuar",
            },
        )

        self.assertEqual(response_pago.status_code, 302)
        transaccion = Transaccion.objects.get()
        transaccion.refresh_from_db()
        self.assertEqual(transaccion.estado, Transaccion.ESTADO_PAGADA)
        self.assertEqual(transaccion.medio_pago, self.medio_pago)
        self.assertIsNotNone(transaccion.fecha_finalizacion)
        self.assertEqual(transaccion.receipt_url, "https://stripe.test/receipt")
        crear_intento.assert_called_once()
        self.assertEqual(crear_intento.call_args.kwargs["payment_method"], "pm_transaccion_test")
        self.assertEqual(crear_intento.call_args.kwargs["amount"], 71000)
        self.assertEqual(crear_intento.call_args.kwargs["currency"], "pyg")

    def test_modal_guarda_como_pendiente_sin_medio_de_pago(self):
        self.client.post(
            reverse("home"),
            {"operation": "venta", "currency": "USD", "amount": "12.5"},
        )
        self.assertFalse(Transaccion.objects.exists())

        response_guardado = self.client.post(
            reverse("transacciones:crear"),
            {
                "operation": "venta",
                "amount": "12.5",
                "currency": "USD",
                "quoted_rate": "7000",
                "accion": "guardar_pendiente",
            },
        )

        self.assertEqual(response_guardado.status_code, 302)
        transaccion = Transaccion.objects.get()
        self.assertEqual(transaccion.estado, Transaccion.ESTADO_PENDIENTE)
        self.assertIsNone(transaccion.medio_pago)
        self.assertIsNone(transaccion.fecha_finalizacion)
        self.assertEqual(transaccion.cantidad_divisa, Decimal("12.50"))

    @patch("apps.stripe.services.stripe.PaymentIntent.create")
    def test_pago_rechazado_permanece_pendiente(self, crear_intento):
        import stripe

        crear_intento.side_effect = stripe.error.CardError(
            "Pago rechazado",
            "param",
            "card_declined",
        )
        response = self.client.post(
            reverse("transacciones:crear"),
            {
                "operation": "compra",
                "amount": "10",
                "currency": "USD",
                "quoted_rate": "7100",
                "medio_pago": self.medio_pago.pk,
                "accion": "efectuar",
            },
        )

        self.assertEqual(response.status_code, 302)
        transaccion = Transaccion.objects.get()
        self.assertEqual(transaccion.estado, Transaccion.ESTADO_PENDIENTE)
        self.assertIsNone(transaccion.medio_pago)
        self.assertFalse(transaccion.receipt_url)

    def test_historial_separa_operaciones_con_pago_y_sin_pago(self):
        pendiente = self.crear_transaccion("HIST-PENDIENTE")
        cancelada = self.crear_transaccion(
            "HIST-CANCELADA",
            estado=Transaccion.ESTADO_CANCELADA,
        )
        pagada = self.crear_transaccion(
            "HIST-PAGADA",
            estado=Transaccion.ESTADO_PAGADA,
            medio_pago=self.medio_pago,
            receipt_url="https://stripe.test/receipt",
        )

        response = self.client.get(reverse("transacciones:historial"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'href="https://stripe.test/receipt"')
        self.assertContains(response, "Ver comprobante de pago")
        self.assertEqual(
            set(response.context["transacciones_sin_pago"].values_list("pk", flat=True)),
            {pendiente.pk, cancelada.pk},
        )
        self.assertEqual(
            list(response.context["transacciones_finalizadas"].values_list("pk", flat=True)),
            [pagada.pk],
        )

    @patch("apps.stripe.services.stripe.PaymentIntent.create")
    def test_pendiente_se_completa_desde_historial(self, crear_intento):
        crear_intento.return_value = Mock(
            id="pi_transaccion_pendiente",
            status="succeeded",
            latest_charge=Mock(receipt_url="https://stripe.test/receipt-pendiente"),
        )
        pendiente = self.crear_transaccion("HIST-COMPLETAR", medio_pago=None)

        response = self.client.post(
            reverse("transacciones:crear"),
            {
                "transaccion_id": pendiente.pk,
                "medio_pago": self.medio_pago.pk,
                "return_to": "historial",
            },
        )

        self.assertRedirects(response, reverse("transacciones:historial"))
        pendiente.refresh_from_db()
        self.assertEqual(pendiente.estado, Transaccion.ESTADO_PAGADA)
        self.assertEqual(pendiente.medio_pago, self.medio_pago)
        self.assertIsNotNone(pendiente.fecha_finalizacion)
        self.assertEqual(
            pendiente.receipt_url,
            "https://stripe.test/receipt-pendiente",
        )

    def crear_transaccion(self, referencia, **kwargs):
        datos = {
            "cliente": self.cliente,
            "monto": Decimal("125.50"),
            "moneda": self.pyg,
            "divisa": self.usd,
            "cantidad_divisa": Decimal("10.00"),
            "tipo_operacion": Transaccion.TIPO_COMPRA,
            "referencia": referencia,
        }
        datos.update(kwargs)
        return Transaccion.objects.create(**datos)