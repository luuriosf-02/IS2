from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.clientes.models import Cliente
from apps.divisas.models import Moneda
from apps.payments.models import MedioPago

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