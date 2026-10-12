from datetime import date
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.users.models import UserClientLink

from .forms import MedioPagoForm
from .models import ClienteStripeCustomer, MedioPago

from django.conf import settings
from django.test import override_settings

User = get_user_model()

TEST_MIDDLEWARE = [
    middleware
    for middleware in settings.MIDDLEWARE
    if middleware
    != "mozilla_django_oidc.middleware.SessionRefresh"
]


class MedioPagoModelTest(TestCase):
    """
    Pruebas unitarias del modelo MedioPago.
    """

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="cliente_test",
            password="password123",
        )

        self.cliente = Cliente.objects.create(
            nombre_razon_social="Cliente de prueba",
            documento="1234567",
            tipo_persona="FISICA",
            categoria="B",
            creado_por=self.usuario,
        )

        self.medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            stripe_payment_method_id="pm_test_4785",
            tipo="DEBITO",
            alias="Tarjeta principal",
            titular="Cliente Test",
            marca="VISA",
            ultimos_cuatro="4242",
            mes_vencimiento=12,
            anio_vencimiento=date.today().year + 1,
            predeterminado=True,
            activo=True,
        )

    def test_crear_medio_pago(self):
        """
        Comprueba que un medio de pago se almacena correctamente.
        """

        self.assertEqual(MedioPago.objects.count(), 1)
        self.assertEqual(
            self.medio_pago.cliente,
            self.cliente,
        )
        self.assertEqual(
            self.medio_pago.ultimos_cuatro,
            "4242",
        )

    def test_representacion_del_medio_pago(self):
        """
        Comprueba el texto generado por el método __str__.
        """

        self.assertEqual(
            str(self.medio_pago),
            "Visa terminada en 4242",
        )


class MedioPagoFormTest(TestCase):
    """
    Pruebas de validación del formulario de medios de pago.
    """

    def datos_validos(self):
        return {
            "tipo": "CREDITO",
            "alias": "Tarjeta personal",
            "titular": "Lujan Rios",
            "marca": "VISA",
            "ultimos_cuatro": "4785",
            "mes_vencimiento": 8,
            "anio_vencimiento": date.today().year + 1,
            "predeterminado": True,
            "activo": True,
        }

    def test_formulario_valido(self):
        """
        Comprueba que el formulario acepta información válida.
        """

        form = MedioPagoForm(data=self.datos_validos())

        self.assertTrue(form.is_valid())

    def test_rechaza_ultimos_cuatro_con_letras(self):
        """
        Comprueba que los últimos cuatro dígitos sean numéricos.
        """

        datos = self.datos_validos()
        datos["ultimos_cuatro"] = "12AB"

        form = MedioPagoForm(data=datos)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "ultimos_cuatro",
            form.errors,
        )

    def test_rechaza_ultimos_cuatro_incompletos(self):
        """
        Comprueba que se ingresen exactamente cuatro dígitos.
        """

        datos = self.datos_validos()
        datos["ultimos_cuatro"] = "123"

        form = MedioPagoForm(data=datos)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "ultimos_cuatro",
            form.errors,
        )

    def test_rechaza_fecha_vencida(self):
        """
        Comprueba que no se acepten medios de pago vencidos.
        """

        datos = self.datos_validos()
        datos["mes_vencimiento"] = 1
        datos["anio_vencimiento"] = date.today().year - 1

        form = MedioPagoForm(data=datos)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "anio_vencimiento",
            form.errors,
        )

@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)

class MedioPagoViewsTest(TestCase):
    """
    Pruebas de las vistas del CRUD de medios de pago.
    """

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario_crud",
            password="password123",
            email="juan.perez@example.com",
        )

        self.cliente = Cliente.objects.create(
            nombre_razon_social="Juan Pérez",
            documento="7654321",
            tipo_persona="FISICA",
            categoria="B",
            activo=True,
            creado_por=self.usuario,
        )

        self.vinculacion = UserClientLink.objects.create(
            user=self.usuario,
            client=self.cliente,
            status=UserClientLink.STATUS_APPROVED,
        )

        self.medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            stripe_payment_method_id="pm_view_test_4785",
            tipo="DEBITO",
            alias="Cédula",
            titular="Juan Pérez",
            marca="VISA",
            ultimos_cuatro="4785",
            mes_vencimiento=8,
            anio_vencimiento=date.today().year + 1,
            predeterminado=True,
            activo=True,
        )

        self.client.force_login(self.usuario)

    def test_listar_medios_pago(self):
        """
        Comprueba que el usuario visualice sus medios de pago.
        """

        response = self.client.get(
            reverse("payments:lista")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visa")
        self.assertContains(response, "4785")
        self.assertNotContains(response, "Editar")

    @patch("apps.stripe.services.stripe.PaymentMethod.list")
    def test_lista_sincroniza_tarjetas_directamente_desde_stripe(
        self,
        listar_payment_methods,
    ):
        ClienteStripeCustomer.objects.create(
            cliente=self.cliente,
            stripe_customer_id="cus_cliente_test",
        )
        payment_method = Mock(id="pm_stripe_list_4242")
        payment_method.to_dict.return_value = {
            "id": "pm_stripe_list_4242",
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 11,
                "exp_year": date.today().year + 2,
            },
            "billing_details": {"name": "Juan Pérez"},
        }
        listar_payment_methods.return_value.auto_paging_iter.return_value = [
            payment_method
        ]

        response = self.client.get(reverse("payments:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "4242")
        listar_payment_methods.assert_called_once_with(
            customer="cus_cliente_test",
            type="card",
            limit=100,
        )
        self.assertTrue(
            MedioPago.objects.filter(
                cliente=self.cliente,
                stripe_payment_method_id="pm_stripe_list_4242",
            ).exists()
        )

    @patch("apps.stripe.views.stripe.checkout.Session.create")
    @patch("apps.stripe.views.stripe.Customer.create")
    def test_crear_medio_de_pago_abre_stripe(
        self,
        crear_customer,
        crear_sesion,
    ):
        crear_customer.return_value.id = "cus_cliente_test"
        crear_sesion.return_value.url = "https://checkout.stripe.test/session"

        response = self.client.post(
            reverse("stripe:create_checkout_session")
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response["Location"],
            "https://checkout.stripe.test/session",
        )
        crear_customer.assert_called_once_with(
            name=self.cliente.nombre_razon_social,
            email=self.usuario.email,
            metadata={"cliente_id": str(self.cliente.pk)},
        )
        crear_sesion.assert_called_once_with(
            mode="setup",
            currency="usd",
            customer="cus_cliente_test",
            success_url=response.wsgi_request.build_absolute_uri(
                reverse("payments:lista")
            ),
            cancel_url=response.wsgi_request.build_absolute_uri(
                reverse("payments:lista")
            ),
        )
        stripe_customer = ClienteStripeCustomer.objects.get(cliente=self.cliente)
        self.assertEqual(stripe_customer.stripe_customer_id, "cus_cliente_test")

    @patch("apps.stripe.views.stripe.checkout.Session.create")
    @patch("apps.stripe.views.stripe.Customer.modify")
    def test_checkout_actualiza_el_email_del_customer_existente(
        self,
        modificar_customer,
        crear_sesion,
    ):
        ClienteStripeCustomer.objects.create(
            cliente=self.cliente,
            stripe_customer_id="cus_cliente_existente",
        )
        crear_sesion.return_value.url = "https://checkout.stripe.test/session"

        response = self.client.post(
            reverse("stripe:create_checkout_session")
        )

        self.assertEqual(response.status_code, 303)
        modificar_customer.assert_called_once_with(
            "cus_cliente_existente",
            email=self.usuario.email,
        )
        crear_sesion.assert_called_once_with(
            mode="setup",
            currency="usd",
            customer="cus_cliente_existente",
            success_url=response.wsgi_request.build_absolute_uri(
                reverse("payments:lista")
            ),
            cancel_url=response.wsgi_request.build_absolute_uri(
                reverse("payments:lista")
            ),
        )

    @patch("apps.stripe.views.stripe.PaymentMethod.detach")
    def test_eliminar_medio_de_pago_lo_desvincula_en_stripe(self, detach):
        response = self.client.post(
            reverse(
                "stripe:delete_payment_method",
                args=[self.medio_pago.pk],
            )
        )

        self.assertRedirects(response, reverse("payments:lista"))
        detach.assert_called_once_with("pm_test_4785")
        self.assertFalse(
            MedioPago.objects.filter(pk=self.medio_pago.pk).exists()
        )

    @patch("apps.stripe.views.stripe.PaymentMethod.retrieve")
    @patch("apps.stripe.views.stripe.Webhook.construct_event")
    def test_webhook_guarda_el_medio_en_el_cliente_de_stripe(
        self,
        construct_event,
        retrieve_payment_method,
    ):
        ClienteStripeCustomer.objects.create(
            cliente=self.cliente,
            stripe_customer_id="cus_cliente_test",
        )
        construct_event.return_value = {
            "type": "setup_intent.succeeded",
            "data": {
                "object": {
                    "customer": "cus_cliente_test",
                    "payment_method": "pm_webhook_test",
                },
            },
        }
        payment_method = Mock(id="pm_webhook_test")
        payment_method.to_dict.return_value = {
            "id": "pm_webhook_test",
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 12,
                "exp_year": date.today().year + 1,
            },
            "billing_details": {"name": "Juan Pérez"},
        }
        retrieve_payment_method.return_value = payment_method

        response = self.client.post(
            reverse("stripe:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        medio_pago = MedioPago.objects.get(
            stripe_payment_method_id="pm_webhook_test"
        )
        self.assertEqual(medio_pago.cliente, self.cliente)
        self.assertEqual(medio_pago.ultimos_cuatro, "4242")

    def test_no_hay_ruta_para_editar_medio_de_pago(self):
        response = self.client.get(
            f"/medios-pago/{self.medio_pago.pk}/editar/"
        )

        self.assertEqual(response.status_code, 404)

@override_settings(MIDDLEWARE=TEST_MIDDLEWARE)

class MedioPagoPermissionsTest(TestCase):
    """
    Pruebas de autenticación y permisos.
    """

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario_sin_vinculacion",
            password="password123",
        )

    def test_redirige_usuario_no_autenticado(self):
        """
        Comprueba que un visitante no pueda acceder al CRUD.
        """

        response = self.client.get(
            reverse("payments:lista")
        )

        self.assertEqual(response.status_code, 302)

    def test_rechaza_usuario_sin_vinculacion(self):
        """
        Comprueba que se rechace un usuario sin vínculo aprobado.
        """

        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse("payments:lista")
        )

        self.assertEqual(response.status_code, 403)

    def test_rechaza_cliente_inactivo(self):
        """
        Comprueba que un usuario con un cliente inactivo vea la indicación correspondiente.
        """

        cliente = Cliente.objects.create(
            nombre_razon_social="Cliente inactivo",
            documento="9999999",
            tipo_persona="FISICA",
            categoria="B",
            creado_por=self.usuario,
            activo=False,
        )
        UserClientLink.objects.create(
            user=self.usuario,
            client=cliente,
            status=UserClientLink.STATUS_APPROVED,
        )

        self.client.force_login(self.usuario)
        response = self.client.get(reverse("payments:lista"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Necesitas un cliente activo")