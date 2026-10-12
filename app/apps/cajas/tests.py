"""Pruebas del módulo independientes de pagos y transacciones."""
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from apps.divisas.models import Moneda
from . import services
from .models import Caja, MovimientoCaja
from .forms import ConteoForm, MovimientoForm


class CajaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='cajero', password='test')
        self.otro = get_user_model().objects.create_user(username='otro', password='test')
        grupo, _ = Group.objects.get_or_create(name='Cajero')
        self.user.groups.add(grupo)
        self.otro.groups.add(grupo)
        self.pyg, _ = Moneda.objects.get_or_create(
            codigo="PYG",
            defaults={"nombre": "Guaraní", "simbolo": "G"},
        )
        self.usd, _ = Moneda.objects.get_or_create(
            codigo="USD",
            defaults={"nombre": "Dólar", "simbolo": "$"},
        )
        self.caja = services.abrir_caja(self.user, {self.pyg.pk: 100, self.usd.pk: 20})

    def mover(self, tipo='egreso', monto=10, clave=None):
        return services.registrar_movimiento(self.user, self.caja.pk, self.pyg.pk, tipo, monto, 'Prueba', clave or uuid.uuid4())

    def saldo(self):
        return self.caja.saldos.get(moneda=self.pyg).actual

    def test_apertura_unica_y_monedas_separadas(self):
        with self.assertRaises(ValidationError):
            services.abrir_caja(self.user, {self.pyg.pk: 1, self.usd.pk: 1})
        self.mover()
        self.assertEqual(self.saldo(), Decimal('90'))
        self.assertEqual(self.caja.saldos.get(moneda=self.usd).actual, Decimal('20'))

    def test_egreso_sin_saldo_no_cambia_nada(self):
        with self.assertRaises(ValidationError):
            self.mover(monto=101)
        self.assertEqual(self.saldo(), Decimal('100'))
        self.assertEqual(MovimientoCaja.objects.count(), 0)

    def test_reenvio_no_duplica(self):
        clave = uuid.uuid4()
        primero = self.mover(clave=clave)
        segundo = self.mover(clave=clave)
        self.assertEqual(primero.pk, segundo.pk)
        self.assertEqual(self.saldo(), Decimal('90'))
        with self.assertRaises(ValidationError):
            self.mover(monto=11, clave=clave)

    def test_anulacion_conserva_y_revierte(self):
        mov = self.mover()
        services.anular_movimiento(self.user, mov.pk, 'Error de carga')
        self.assertEqual(self.saldo(), Decimal('100'))
        self.assertEqual(MovimientoCaja.objects.count(), 1)
        with self.assertRaises(ValidationError):
            services.anular_movimiento(self.user, mov.pk, 'Otra vez')

    def test_ingreso_gastado_no_se_puede_anular(self):
        mov = self.mover(tipo='ingreso', monto=10)
        self.mover(monto=110)
        with self.assertRaises(ValidationError):
            services.anular_movimiento(self.user, mov.pk, 'Error')
        self.assertEqual(self.saldo(), Decimal('0'))

    def test_cierre_diferencia_y_bloqueo(self):
        with self.assertRaises(ValidationError):
            services.cerrar_caja(self.user, self.caja.pk, {self.pyg.pk: 99, self.usd.pk: 20})
        services.cerrar_caja(self.user, self.caja.pk, {self.pyg.pk: 99, self.usd.pk: 20}, 'Faltante contado')
        saldo = self.caja.saldos.get(moneda=self.pyg)
        self.assertEqual(saldo.diferencia, Decimal('-1'))
        with self.assertRaises(ValidationError):
            self.mover()
        nueva = services.abrir_caja(self.user, {self.pyg.pk: 99, self.usd.pk: 20})
        self.assertNotEqual(nueva.pk, self.caja.pk)

    def test_permisos_y_caja_ajena(self):
        with self.assertRaises(PermissionDenied):
            services.registrar_movimiento(self.otro, self.caja.pk, self.pyg.pk, 'ingreso', 1, 'Error', uuid.uuid4())
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(reverse('cajas:detalle', args=[self.caja.pk])).status_code, 404)
        self.otro.groups.clear()
        self.assertEqual(self.client.get(reverse('cajas:lista')).status_code, 403)

    def test_importes_invalidos(self):
        for valor in ['NaN', 'Infinity', '-1', '0.001', '10000000000000000']:
            with self.assertRaises(ValidationError):
                self.mover(monto=valor)
        self.assertEqual(self.saldo(), Decimal('100'))

    def test_formularios(self):
        form = MovimientoForm({'moneda': self.pyg.pk, 'tipo': 'ingreso', 'monto': '1.50', 'concepto': 'Carga', 'referencia': '', 'clave': str(uuid.uuid4())}, caja=self.caja)
        self.assertTrue(form.is_valid(), form.errors)
        cierre = ConteoForm({'moneda_' + str(self.pyg.pk): '100', 'moneda_' + str(self.usd.pk): '20', 'observacion': ''}, caja=self.caja)
        self.assertTrue(cierre.is_valid(), cierre.errors)
