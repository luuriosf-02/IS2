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