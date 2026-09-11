from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.divisas.models import Moneda, TasaCambio, Notificacion
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
        response_editar = gestion_divisas_view(editar_request)

        self.assertEqual(response_editar.status_code, 302)
        tasa.refresh_from_db()
        self.assertEqual(float(tasa.tasa_compra), 7600.5)
        self.assertEqual(float(tasa.tasa_venta), 7700.75)

        delete_request = factory.post(
            '/divisas/gestion-tasas/',
            {'action': 'eliminar_tasa', 'tasa_id': str(tasa.pk)}
        )
        delete_request.user = user
        response_delete = gestion_divisas_view(delete_request)

        self.assertEqual(response_delete.status_code, 302)
        self.assertFalse(TasaCambio.objects.filter(pk=tasa.pk).exists())