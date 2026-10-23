import uuid
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from apps.divisas.models import Moneda, TasaCambio
from .models import Caja, SaldoCaja, MovimientoCaja, CambioCaja
from . import services


class CajasActualizadasTest(TestCase):
    def setUp(self):
        U = get_user_model()
        self.admin = U.objects.create_user(username='admin_cajas_qa', is_staff=True)
        self.cajero = U.objects.create_user(username='cajero_cajas_qa')
        self.otro = U.objects.create_user(username='otro_cajas_qa')
        grupo, _ = Group.objects.get_or_create(name='Cajero')
        self.cajero.groups.add(grupo)
        self.otro.groups.add(grupo)
        self.pyg, _ = Moneda.objects.update_or_create(codigo='PYG', defaults={'nombre':'Guaraní','simbolo':'G','activa':True})
        self.usd, _ = Moneda.objects.update_or_create(codigo='USD', defaults={'nombre':'Dólar','simbolo':'$','activa':True})
        self.tasa = TasaCambio.objects.create(moneda=self.usd, tasa_compra=7800, tasa_venta=8000)
        self.montos = {m.pk: Decimal('0') for m in Moneda.objects.filter(activa=True)}
        self.montos.update({self.pyg.pk: Decimal('1000000'), self.usd.pk: Decimal('500')})
        self.caja = services.abrir_caja(self.admin, self.cajero, self.montos)
        services.aceptar_caja(self.cajero, self.caja.pk, self.montos)

    def token(self, origen=None, destino=None, monto='800000', clave=None):
        return services.preparar_cambio(self.cajero, self.caja.pk,
            (origen or self.pyg).pk, (destino or self.usd).pk, monto, clave or uuid.uuid4())[1]

    def saldos(self):
        return dict(self.caja.saldos.values_list('moneda_id', 'actual'))

    def test_apertura_asignada_por_administrador(self):
        self.assertEqual(self.caja.abierta_por, self.admin)
        self.assertEqual(self.caja.cajero, self.cajero)

    def test_cajero_no_puede_abrir(self):
        with self.assertRaises(PermissionDenied):
            services.abrir_caja(self.cajero, self.otro, self.montos)

    def test_no_dos_cajas_abiertas(self):
        with self.assertRaises(ValidationError):
            services.abrir_caja(self.admin, self.cajero, self.montos)

    def test_no_asignar_a_cliente(self):
        cliente = get_user_model().objects.create_user(username='cliente_cajas_qa')
        with self.assertRaises(ValidationError):
            services.abrir_caja(self.admin, cliente, self.montos)

    def test_guaranies_a_dolares(self):
        c = services.confirmar_cambio(self.cajero, self.caja.pk, self.token())
        self.assertEqual(c.monto_entregado, Decimal('100'))
        self.assertEqual(c.tipo_tasa, 'venta')
        self.assertEqual(self.saldos()[self.pyg.pk], Decimal('1800000'))
        self.assertEqual(self.saldos()[self.usd.pk], Decimal('400'))
        self.assertEqual(c.movimientos.count(), 2)

    def test_dolares_a_guaranies(self):
        c = services.confirmar_cambio(self.cajero, self.caja.pk, self.token(self.usd, self.pyg, '100'))
        self.assertEqual(c.monto_entregado, Decimal('780000'))
        self.assertEqual(c.tipo_tasa, 'compra')
        self.assertEqual(self.saldos()[self.usd.pk], Decimal('600'))
        self.assertEqual(self.saldos()[self.pyg.pk], Decimal('220000'))

    def test_insuficiente_no_cambia_nada(self):
        antes = self.saldos()
        with self.assertRaises(ValidationError):
            services.confirmar_cambio(self.cajero, self.caja.pk, self.token(monto='4800000'))
        self.assertEqual(self.saldos(), antes)
        self.assertFalse(CambioCaja.objects.exists())
        self.assertFalse(MovimientoCaja.objects.exists())

    def test_reenvio_no_duplica(self):
        token = self.token()
        a = services.confirmar_cambio(self.cajero, self.caja.pk, token)
        b = services.confirmar_cambio(self.cajero, self.caja.pk, token)
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(MovimientoCaja.objects.count(), 2)

    def test_tasa_cambia_exige_recalcular(self):
        token = self.token()
        self.tasa.tasa_venta = 8100
        self.tasa.save()
        with self.assertRaises(ValidationError):
            services.confirmar_cambio(self.cajero, self.caja.pk, token)
        self.assertFalse(CambioCaja.objects.exists())

    def test_anular_movimiento_revierte_cambio_entero(self):
        antes = self.saldos()
        c = services.confirmar_cambio(self.cajero, self.caja.pk, self.token())
        services.anular_movimiento(self.cajero, c.movimientos.first().pk, 'Error de carga')
        self.assertEqual(self.saldos(), antes)
        self.assertEqual(c.movimientos.filter(anulado_en__isnull=False).count(), 2)
        with self.assertRaises(ValidationError):
            services.anular_cambio(self.cajero, c.pk, 'Repetido')

    def test_anulacion_sin_saldo_no_revierte_parcialmente(self):
        c = services.confirmar_cambio(self.cajero, self.caja.pk, self.token())
        services.registrar_movimiento(self.cajero, self.caja.pk, self.pyg.pk, 'egreso', '1500000', 'Retiro', uuid.uuid4())
        antes = self.saldos()
        with self.assertRaises(ValidationError):
            services.anular_cambio(self.cajero, c.pk, 'Corrección')
        self.assertEqual(self.saldos(), antes)
        self.assertEqual(c.movimientos.filter(anulado_en__isnull=False).count(), 0)

    def test_no_operar_caja_ajena(self):
        with self.assertRaises(PermissionDenied):
            services.confirmar_cambio(self.otro, self.caja.pk, self.token())

    def test_cierre_bloquea_cambios(self):
        token = self.token()
        services.cerrar_caja(self.cajero, self.caja.pk, self.saldos())
        with self.assertRaises(ValidationError):
            services.confirmar_cambio(self.cajero, self.caja.pk, token)

    def test_firma_manipulada(self):
        with self.assertRaises(ValidationError):
            services.confirmar_cambio(self.cajero, self.caja.pk, self.token()+'x')

    def test_monedas_iguales_y_tasa_cero(self):
        with self.assertRaises(ValidationError):
            services.cotizar_cambio(self.pyg.pk, self.pyg.pk, '10')
        self.tasa.tasa_venta = 0
        self.tasa.save()
        with self.assertRaises(ValidationError):
            self.token()

    def test_vistas_admin_cajero_y_formulario(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('cajas:lista'))
        self.assertContains(response, 'Asignar caja y fondos')
        self.assertEqual(self.client.get(reverse('cajas:apertura')).status_code, 200)
        self.assertEqual(self.client.get(reverse('cajas:detalle', args=[self.caja.pk])).status_code, 200)
        self.client.force_login(self.cajero)
        self.assertEqual(self.client.get(reverse('cajas:apertura')).status_code, 403)
        self.assertNotContains(self.client.get(reverse('cajas:lista')), 'Asignar caja y fondos')
        self.assertContains(self.client.get(reverse('cajas:detalle', args=[self.caja.pk])), 'Realizar cambio')
        url = reverse('cajas:cambio', args=[self.caja.pk])
        response = self.client.post(url, {'moneda_recibida':self.pyg.pk, 'moneda_entregada':self.usd.pk,
            'monto':'800000','clave':str(uuid.uuid4()),'referencia':'OP-1','accion':'calcular'})
        self.assertContains(response, 'Confirmar operación')
        token = response.context['confirmacion'].initial['cotizacion']
        self.assertEqual(self.client.post(url, {'accion':'confirmar','cotizacion':token}).status_code, 302)
        self.assertEqual(CambioCaja.objects.count(), 1)

    def test_movimiento_manual_y_cierre_con_diferencia(self):
        services.registrar_movimiento(self.cajero, self.caja.pk, self.usd.pk, 'ingreso', '10', 'Reposición', uuid.uuid4())
        conteo = self.saldos(); conteo[self.usd.pk] -= 1
        with self.assertRaises(ValidationError):
            services.cerrar_caja(self.cajero, self.caja.pk, conteo)
        services.cerrar_caja(self.cajero, self.caja.pk, conteo, 'Faltante de un dólar')
        self.assertEqual(self.caja.saldos.get(moneda=self.usd).diferencia, Decimal('-1'))

    def test_fallo_al_crear_movimientos_revierte_saldos(self):
        from unittest.mock import patch
        antes = self.saldos()
        with patch('apps.cajas.services.MovimientoCaja.objects.create', side_effect=RuntimeError('fallo simulado')):
            with self.assertRaises(RuntimeError):
                services.confirmar_cambio(self.cajero, self.caja.pk, self.token())
        self.assertEqual(self.saldos(), antes)
        self.assertFalse(CambioCaja.objects.exists())

    def test_redondeo_y_cotizacion_vencida(self):
        from unittest.mock import patch
        c = services.cotizar_cambio(self.pyg.pk, self.usd.pk, '100000')
        self.assertEqual(c['resultado'], Decimal('12.50'))
        with patch('django.core.signing.time.time', return_value=1000):
            token = self.token()
        with patch('django.core.signing.time.time', return_value=1601):
            with self.assertRaises(ValidationError):
                services.confirmar_cambio(self.cajero, self.caja.pk, token)
        self.assertFalse(CambioCaja.objects.exists())

    def test_moneda_desactivada_tras_cotizar(self):
        token = self.token()
        self.usd.activa = False
        self.usd.save()
        with self.assertRaises(ValidationError):
            services.confirmar_cambio(self.cajero, self.caja.pk, token)
        self.assertFalse(CambioCaja.objects.exists())


class AceptacionCajaTest(TestCase):
    def setUp(self):
        CajasActualizadasTest.setUp(self)
        self.pendiente = services.abrir_caja(self.admin, self.otro, self.montos)

    def test_asignacion_queda_pendiente(self):
        self.assertFalse(self.pendiente.habilitada)
        self.assertEqual(self.pendiente.estado, 'Pendiente de aceptación')
        self.assertIsNone(self.pendiente.aceptada_en)

    def test_solo_cajero_asignado_puede_aceptar(self):
        for usuario in [self.cajero, self.admin]:
            with self.assertRaises(PermissionDenied):
                services.aceptar_caja(usuario, self.pendiente.pk, self.montos)
        self.assertFalse(self.pendiente.conteos_iniciales.exists())

    def test_diferencias_se_guardan_sin_habilitar(self):
        montos = dict(self.montos); montos[self.usd.pk] = Decimal('490')
        conteo = services.aceptar_caja(self.otro, self.pendiente.pk, montos, 'Faltan diez dólares')
        self.pendiente.refresh_from_db()
        self.assertFalse(conteo.coincide)
        self.assertFalse(self.pendiente.habilitada)
        self.assertEqual(conteo.detalles.get(moneda=self.usd).diferencia, Decimal('-10'))
        self.assertEqual(self.pendiente.saldos.get(moneda=self.usd).actual, Decimal('500'))
        self.assertIsNone(self.pendiente.saldos.get(moneda=self.usd).contado)

    def test_reconteo_correcto_habilita_y_conserva_intento_anterior(self):
        montos = dict(self.montos); montos[self.usd.pk] = Decimal('490')
        services.aceptar_caja(self.otro, self.pendiente.pk, montos)
        conteo = services.aceptar_caja(self.otro, self.pendiente.pk, self.montos)
        self.pendiente.refresh_from_db()
        self.assertTrue(conteo.coincide)
        self.assertTrue(self.pendiente.habilitada)
        self.assertEqual(self.pendiente.aceptada_por, self.otro)
        self.assertIsNotNone(self.pendiente.aceptada_en)
        self.assertEqual(self.pendiente.conteos_iniciales.count(), 2)
        mov = services.registrar_movimiento(self.otro, self.pendiente.pk, self.usd.pk, 'ingreso', '10', 'Reposición', uuid.uuid4())
        self.assertEqual(mov.monto, Decimal('10'))

    def test_aceptacion_no_se_repite(self):
        services.aceptar_caja(self.otro, self.pendiente.pk, self.montos)
        with self.assertRaises(ValidationError):
            services.aceptar_caja(self.otro, self.pendiente.pk, self.montos)
        self.assertEqual(self.pendiente.conteos_iniciales.count(), 1)

    def test_pendiente_bloquea_movimientos_cierre_y_cotizacion(self):
        with self.assertRaises(ValidationError):
            services.registrar_movimiento(self.otro, self.pendiente.pk, self.usd.pk, 'egreso', '10', 'Retiro', uuid.uuid4())
        with self.assertRaises(ValidationError):
            services.cerrar_caja(self.otro, self.pendiente.pk, self.montos)
        with self.assertRaises(ValidationError):
            services.preparar_cambio(self.otro, self.pendiente.pk, self.pyg.pk, self.usd.pk, '800000', uuid.uuid4())
        self.assertFalse(self.pendiente.movimientos.exists())

    def test_pendiente_bloquea_confirmacion_firmada(self):
        from django.core import signing
        token = signing.dumps({'usuario':self.otro.pk, 'caja':self.pendiente.pk}, salt=services.SALT_CAMBIO)
        with self.assertRaises(ValidationError):
            services.confirmar_cambio(self.otro, self.pendiente.pk, token)
        self.assertFalse(self.pendiente.cambios.exists())

    def test_conteo_incompleto_negativo_o_invalido_no_se_guarda(self):
        for montos in [{}, {**self.montos, self.usd.pk:Decimal('-1')}, {**self.montos, self.usd.pk:Decimal('NaN')}]:
            with self.assertRaises(ValidationError):
                services.aceptar_caja(self.otro, self.pendiente.pk, montos)
        self.assertFalse(self.pendiente.conteos_iniciales.exists())

    def test_no_dos_asignaciones_pendientes(self):
        with self.assertRaises(ValidationError):
            services.abrir_caja(self.admin, self.otro, self.montos)

    def test_vistas_conteo_diferencia_y_aceptacion(self):
        self.client.force_login(self.otro)
        detalle = reverse('cajas:detalle', args=[self.pendiente.pk])
        aceptar = reverse('cajas:aceptacion', args=[self.pendiente.pk])
        self.assertContains(self.client.get(detalle), 'Contar y aceptar caja')
        self.assertNotContains(self.client.get(detalle), '>Realizar cambio<')
        self.assertEqual(self.client.get(aceptar).context['form'].fields[f'moneda_{self.usd.pk}'].initial, 0)
        for ruta in ['movimiento','cambio','cierre']:
            self.assertRedirects(self.client.get(reverse('cajas:'+ruta, args=[self.pendiente.pk])), aceptar)
        datos = {f'moneda_{k}':str(v) for k,v in self.montos.items()}
        datos[f'moneda_{self.usd.pk}'] = '490'
        self.assertRedirects(self.client.post(aceptar, datos), detalle)
        self.assertContains(self.client.get(detalle), 'Con diferencias: no aceptada')
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(detalle), '-10')
        self.assertEqual(self.client.get(aceptar).status_code, 403)
        self.client.force_login(self.otro)
        datos[f'moneda_{self.usd.pk}'] = '500'
        self.assertRedirects(self.client.post(aceptar, datos), detalle)
        self.assertContains(self.client.get(detalle), '>Realizar cambio<')

    def test_caja_cerrada_no_acepta(self):
        with self.assertRaises(ValidationError):
            self.caja.refresh_from_db()
            services.cerrar_caja(self.cajero, self.caja.pk, self.montos)
            services.aceptar_caja(self.cajero, self.caja.pk, self.montos)
