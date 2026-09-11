from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.users.models import UserClientLink

from .forms import MedioPagoForm
from .models import MedioPago

from django.conf import settings
from django.test import TestCase, override_settings

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
        )

        self.cliente = Cliente.objects.create(
            nombre_razon_social="Juan Pérez",
            documento="7654321",
            tipo_persona="FISICA",
            categoria="B",
            creado_por=self.usuario,
        )

        self.vinculacion = UserClientLink.objects.create(
            user=self.usuario,
            client=self.cliente,
            status=UserClientLink.STATUS_APPROVED,
        )

        self.medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
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

    def datos_medio_pago(self):
        return {
            "tipo": "CREDITO",
            "alias": "Nueva tarjeta",
            "titular": "Juan Pérez",
            "marca": "MASTERCARD",
            "ultimos_cuatro": "1234",
            "mes_vencimiento": 10,
            "anio_vencimiento": date.today().year + 2,
            "predeterminado": "on",
            "activo": "on",
        }

    def test_listar_medios_pago(self):
        """
        Comprueba que el usuario visualice sus medios de pago.
        """

        response = self.client.get(
            reverse("payments:lista")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cédula")
        self.assertContains(response, "4785")

    def test_crear_medio_pago(self):
        """
        Comprueba la creación mediante la vista.
        """

        response = self.client.post(
            reverse("payments:crear"),
            data=self.datos_medio_pago(),
        )

        self.assertRedirects(
            response,
            reverse("payments:lista"),
        )

        self.assertTrue(
            MedioPago.objects.filter(
                cliente=self.cliente,
                ultimos_cuatro="1234",
            ).exists()
        )

    def test_editar_medio_pago(self):
        """
        Comprueba la modificación mediante la vista.
        """

        datos = self.datos_medio_pago()
        datos["alias"] = "Tarjeta actualizada"

        response = self.client.post(
            reverse(
                "payments:editar",
                args=[self.medio_pago.pk],
            ),
            data=datos,
        )

        self.assertRedirects(
            response,
            reverse("payments:lista"),
        )

        self.medio_pago.refresh_from_db()

        self.assertEqual(
            self.medio_pago.alias,
            "Tarjeta actualizada",
        )

    def test_eliminar_medio_pago(self):
        """
        Comprueba la eliminación mediante la vista.
        """

        response = self.client.post(
            reverse(
                "payments:eliminar",
                args=[self.medio_pago.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("payments:lista"),
        )

        self.assertFalse(
            MedioPago.objects.filter(
                pk=self.medio_pago.pk
            ).exists()
        )

    def test_un_solo_medio_predeterminado(self):
        """
        Comprueba que solamente exista un medio predeterminado.
        """

        self.client.post(
            reverse("payments:crear"),
            data=self.datos_medio_pago(),
        )

        self.medio_pago.refresh_from_db()

        self.assertFalse(
            self.medio_pago.predeterminado
        )

        self.assertEqual(
            MedioPago.objects.filter(
                cliente=self.cliente,
                predeterminado=True,
            ).count(),
            1,
        )

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