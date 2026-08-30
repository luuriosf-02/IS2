from django.test import TestCase
from clientes.models import Cliente

class ClienteModelTest(TestCase):
    """
    Pruebas unitarias para la validación de la clasificación y categorización de clientes.
    """
    def setUp(self):
        self.cliente_fisico = Cliente.objects.create(
            nombre_razon_social="Juan Pérez",
            documento="1234567",
            tipo_persona="FISICA",
            categoria="B"
        )

    def test_creacion_cliente_fisico(self):
        self.assertEqual(self.cliente_fisico.tipo_persona, "FISICA")
        self.assertTrue(self.cliente_fisico.activo)

    def test_creacion_cliente_juridico(self):
        cliente_corp = Cliente.objects.create(
            nombre_razon_social="Global Exchange S.A.",
            documento="80012345-6",
            tipo_persona="JURIDICA",
            categoria="A"
        )
        self.assertEqual(cliente_corp.categoria, "A")