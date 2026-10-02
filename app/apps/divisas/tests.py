from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse
from apps.clientes.models import Cliente
from apps.divisas.models import Moneda, TasaCambio, Notificacion
from apps.payments.models import MedioPago
from apps.transacciones.models import Transaccion
from apps.divisas.views import gestion_divisas_view
from apps.users.models import Profile

User = get_user_model()

class DivisasTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123',
            is_active=True
        )
        self.moneda = Moneda.objects.create(
            codigo='USD', 
            nombre='Dólar Estadounidense', 
            simbolo='$', 
            activa=True
        )

    def test_creacion_moneda(self):
        """Verifica la correcta creación de una moneda."""
        self.assertEqual(self.moneda.codigo, 'USD')
        self.assertTrue(self.moneda.activa)

    def test_actualizacion_tasa_y_notificacion(self):
        """Verifica que al guardar una TasaCambio se cree la Notificacion in-app via Signal (SCRUM-67)."""
        tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            tasa_compra=7500.00,
            tasa_venta=7550.00,
            usuario_modificador=self.user
        )
        self.assertEqual(tasa.tasa_compra, 7500.00)
        self.assertTrue(Notificacion.objects.filter(usuario=self.user).exists())

    def test_analista_puede_acceder_por_profile_role(self):
        """El acceso debe validarse con el rol guardado en Profile, no solo con grupos de Django."""
        factory = RequestFactory()
        user = User.objects.create_user(
            username='analista_perfil',
            email='analista@example.com',
            password='password123',
            is_active=True,
        )
        Profile.objects.create(user=user, role='Analista Cambiario')

        request = factory.get('/divisas/gestion-tasas/')
        request.user = user

        response = gestion_divisas_view(request)

        self.assertEqual(response.status_code, 200)

    def test_crear_moneda_y_tasa_desde_la_vista(self):
        """La vista debe permitir dar de alta monedas y luego asignarles tasas desde las monedas existentes."""
        factory = RequestFactory()
        user = User.objects.create_user(
            username='analista_crear',
            email='analista.crear@example.com',
            password='password123',
            is_active=True,
        )
        Profile.objects.create(user=user, role='Analista Cambiario')

        moneda_request = factory.post(
            '/divisas/gestion-tasas/',
            {
                'action': 'crear_moneda',
                'codigo': 'EUR',
                'nombre': 'Euro',
                'simbolo': '€',
                'activa': 'on',
            }
        )
        moneda_request.user = user
        response_moneda = gestion_divisas_view(moneda_request)

        self.assertEqual(response_moneda.status_code, 302)
        self.assertTrue(Moneda.objects.filter(codigo='EUR', nombre='Euro').exists())

        moneda = Moneda.objects.get(codigo='EUR')
        tasa_request = factory.post(
            '/divisas/gestion-tasas/',
            {
                'action': 'crear_tasa',
                'moneda': str(moneda.pk),
                'tasa_compra': '7200.1234',
                'tasa_venta': '7300.5678',
            }
        )
        tasa_request.user = user
        response_tasa = gestion_divisas_view(tasa_request)

        self.assertEqual(response_tasa.status_code, 302)
        self.assertTrue(TasaCambio.objects.filter(moneda=moneda).exists())

    def test_editar_y_eliminar_tasa_desde_la_vista(self):
        """La vista debe permitir modificar y borrar una tasa existente."""
        factory = RequestFactory()
        user = User.objects.create_user(
            username='analista_crud',
            email='analista.crud@example.com',
            password='password123',
            is_active=True,
        )
        Profile.objects.create(user=user, role='Analista Cambiario')

        moneda = Moneda.objects.create(codigo='BRL', nombre='Real Brasileño', simbolo='R$', activa=True)
        tasa = TasaCambio.objects.create(
            moneda=moneda,
            tasa_compra=7000.00,
            tasa_venta=7100.00,
            usuario_modificador=user,
        )
        cliente = Cliente.objects.create(
            nombre_razon_social='Cliente de prueba',
            documento='divisas-transaccion-123',
            creado_por=user,
        )
        medio_pago = MedioPago.objects.create(
            cliente=cliente,
            tipo='DEBITO',
            alias='Tarjeta principal',
            titular='Cliente Test',
            marca='VISA',
            ultimos_cuatro='4242',
            mes_vencimiento=12,
            anio_vencimiento=2099,
        )
        transaccion_pendiente = Transaccion.objects.create(
            cliente=cliente,
            medio_pago=medio_pago,
            monto=100,
            moneda=moneda,
            divisa=moneda,
            referencia='DIVISAS-PENDIENTE',
        )
        transaccion_otra_divisa = Transaccion.objects.create(
            cliente=cliente,
            medio_pago=medio_pago,
            monto=100,
            moneda=moneda,
            divisa=self.moneda,
            referencia='DIVISAS-OTRA',
        )
        transaccion_no_pendiente = Transaccion.objects.create(
            cliente=cliente,
            medio_pago=medio_pago,
            monto=100,
            moneda=moneda,
            divisa=moneda,
            referencia='DIVISAS-PAGADA',
            estado=Transaccion.ESTADO_PAGADA,
        )

        editar_request = factory.post(
            '/divisas/gestion-tasas/',
            {
                'action': 'editar_tasa',
                'tasa_id': str(tasa.pk),
                'moneda': str(moneda.pk),
                'tasa_compra': '7600.5',
                'tasa_venta': '7700.75',
            }
        )
        editar_request.user = user
        editar_request.session = {}
        editar_request._messages = FallbackStorage(editar_request)
        response_editar = gestion_divisas_view(editar_request)

        self.assertEqual(response_editar.status_code, 302)
        tasa.refresh_from_db()
        self.assertEqual(float(tasa.tasa_compra), 7600.5)
        self.assertEqual(float(tasa.tasa_venta), 7700.75)
        transaccion_pendiente.refresh_from_db()
        transaccion_otra_divisa.refresh_from_db()
        transaccion_no_pendiente.refresh_from_db()
        self.assertEqual(transaccion_pendiente.estado, Transaccion.ESTADO_CANCELADA)
        self.assertIsNotNone(transaccion_pendiente.fecha_finalizacion)
        self.assertEqual(transaccion_otra_divisa.estado, Transaccion.ESTADO_PENDIENTE)
        self.assertEqual(transaccion_no_pendiente.estado, Transaccion.ESTADO_PAGADA)

        transaccion_sin_cambio = Transaccion.objects.create(
            cliente=cliente,
            medio_pago=medio_pago,
            monto=100,
            moneda=moneda,
            divisa=moneda,
            referencia='DIVISAS-SIN-CAMBIO',
        )
        sin_cambios_request = factory.post(
            '/divisas/gestion-tasas/',
            {
                'action': 'editar_tasa',
                'tasa_id': str(tasa.pk),
                'moneda': str(moneda.pk),
                'tasa_compra': '7600.5',
                'tasa_venta': '7700.75',
            }
        )
        sin_cambios_request.user = user
        sin_cambios_request.session = {}
        sin_cambios_request._messages = FallbackStorage(sin_cambios_request)
        response_sin_cambios = gestion_divisas_view(sin_cambios_request)

        self.assertEqual(response_sin_cambios.status_code, 302)
        transaccion_sin_cambio.refresh_from_db()
        self.assertEqual(
            transaccion_sin_cambio.estado,
            Transaccion.ESTADO_PENDIENTE,
        )

        delete_request = factory.post(
            '/divisas/gestion-tasas/',
            {'action': 'eliminar_tasa', 'tasa_id': str(tasa.pk)}
        )
        delete_request.user = user
        delete_request.session = {}
        delete_request._messages = FallbackStorage(delete_request)
        response_delete = gestion_divisas_view(delete_request)

        self.assertEqual(response_delete.status_code, 302)
        self.assertFalse(TasaCambio.objects.filter(pk=tasa.pk).exists())

    def test_nueva_cotizacion_cancela_y_se_visualiza_en_historial(self):
        user = User.objects.create_user(
            username='analista_nueva_cotizacion',
            email='analista.nueva@example.com',
            password='password123',
        )
        Profile.objects.create(user=user, role='Analista Cambiario')
        TasaCambio.objects.create(
            moneda=self.moneda,
            tasa_compra=7000,
            tasa_venta=7100,
            usuario_modificador=user,
        )
        cliente = Cliente.objects.create(
            nombre_razon_social='Cliente historial',
            documento='divisas-historial-123',
            creado_por=user,
            activo=True,
        )
        medio_pago = MedioPago.objects.create(
            cliente=cliente,
            tipo='DEBITO',
            alias='Tarjeta principal',
            titular='Cliente Test',
            marca='VISA',
            ultimos_cuatro='4242',
            mes_vencimiento=12,
            anio_vencimiento=2099,
        )
        transaccion = Transaccion.objects.create(
            cliente=cliente,
            medio_pago=medio_pago,
            monto=100,
            moneda=self.moneda,
            divisa=self.moneda,
            referencia='DIVISAS-HISTORIAL-CANCELADA',
        )

        self.client.force_login(
            user,
            backend='django.contrib.auth.backends.ModelBackend',
        )
        respuesta_tasa = self.client.post(
            reverse('gestion_divisas'),
            {
                'action': 'crear_tasa',
                'moneda': str(self.moneda.pk),
                'tasa_compra': '7200',
                'tasa_venta': '7300',
            },
        )

        self.assertEqual(respuesta_tasa.status_code, 302)
        transaccion.refresh_from_db()
        self.assertEqual(transaccion.estado, Transaccion.ESTADO_CANCELADA)
        self.assertIsNotNone(transaccion.fecha_finalizacion)

        respuesta_historial = self.client.get(reverse('transacciones:historial'))

        self.assertEqual(respuesta_historial.status_code, 200)
        self.assertContains(respuesta_historial, 'DIVISAS-HISTORIAL-CANCELADA')
        self.assertContains(respuesta_historial, 'transaction-status-cancelada')
        self.assertContains(respuesta_historial, 'Cancelada')