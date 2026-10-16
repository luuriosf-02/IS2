from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase, Client
from django.urls import reverse
from .models import Moneda, TasaCambio, Notificacion

class NotificacionesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.a = User.objects.create_user(username='cliente-a', email='a@example.com')
        self.b = User.objects.create_user(username='cliente-b', email='b@example.com')
        self.inactivo = User.objects.create_user(username='inactivo', is_active=False)
        self.moneda = Moneda.objects.create(codigo='USD', nombre='Dólar', simbolo='$')

    def crear(self, compra='7200', venta='7300'):
        return TasaCambio.objects.create(moneda=self.moneda, tasa_compra=compra, tasa_venta=venta)

    def test_primera_tasa_y_destinatarios(self):
        self.crear()
        self.assertEqual(Notificacion.objects.count(), 2)
        self.assertFalse(Notificacion.objects.filter(usuario=self.inactivo).exists())

    def test_mismos_valores_no_duplican(self):
        tasa = self.crear()
        tasa.save()
        self.crear()
        self.assertEqual(Notificacion.objects.count(), 2)

    def test_edicion_muestra_anterior_y_actual(self):
        tasa = self.crear()
        tasa.tasa_compra = Decimal('7250')
        tasa.save()
        self.assertEqual(Notificacion.objects.count(), 4)
        aviso = Notificacion.objects.order_by('-pk').first()
        self.assertIn('7200', aviso.mensaje)
        self.assertIn('7250', aviso.mensaje)

    def test_nueva_fila_con_cambio(self):
        self.crear()
        self.crear('7250')
        self.assertEqual(Notificacion.objects.count(), 4)

    def test_rollback_no_notifica(self):
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(ValueError):
                with transaction.atomic():
                    self.crear()
                    raise ValueError('rollback')
        self.assertEqual(Notificacion.objects.count(), 0)

    def test_listado_solo_propio(self):
        self.crear()
        self.client.force_login(self.a)
        respuesta = self.client.get(reverse('notificaciones:lista'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['no_leidas'], 1)
        self.assertEqual(len(respuesta.json()['notificaciones']), 1)

    def test_no_puede_leer_ajeno(self):
        self.crear()
        self.client.force_login(self.a)
        otro = Notificacion.objects.get(usuario=self.b)
        r = self.client.post(reverse('notificaciones:leer', args=[otro.pk]))
        self.assertEqual(r.status_code, 404)
        otro.refresh_from_db()
        self.assertFalse(otro.leida)

    def test_marcar_individual_y_todas(self):
        self.crear()
        self.client.force_login(self.a)
        aviso = Notificacion.objects.get(usuario=self.a)
        url = reverse('notificaciones:leer', args=[aviso.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(self.client.get(reverse('notificaciones:lista')).json()['no_leidas'], 0)
        self.crear('7250')
        self.client.post(reverse('notificaciones:leer_todas'))
        self.assertFalse(Notificacion.objects.filter(usuario=self.a, leida=False).exists())
        self.assertTrue(Notificacion.objects.filter(usuario=self.b, leida=False).exists())

    def test_anonimo_y_csrf(self):
        self.assertEqual(self.client.get(reverse('notificaciones:lista')).status_code, 302)
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.a)
        self.assertEqual(secure.post(reverse('notificaciones:leer_todas')).status_code, 403)
