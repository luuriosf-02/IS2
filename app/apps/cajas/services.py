"""Operaciones atómicas de efectivo. No confirman pagos electrónicos."""
from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from apps.divisas.models import Moneda
from .models import Caja, SaldoCaja, MovimientoCaja, CambioCaja, ConteoInicial, DetalleConteoInicial

MAXIMO = Decimal('9999999999999999.99')


def puede_operar(user):
    return bool(user.is_authenticated and user.is_active and (
        user.is_superuser or
        getattr(getattr(user, 'profile', None), 'role', '') == 'Cajero' or
        user.groups.filter(name='Cajero').exists()
    ))


def puede_administrar(user):
    return bool(user.is_authenticated and user.is_active and (
        user.is_staff or user.is_superuser or
        getattr(getattr(user, 'profile', None), 'role', '') == 'Administrador'
    ))


def autorizar_admin(user):
    if not puede_administrar(user):
        raise PermissionDenied('Solo el administrador puede asignar cajas y saldos iniciales.')


def es_cajero(user):
    return bool(user.is_active and (
        getattr(getattr(user, 'profile', None), 'role', '') == 'Cajero' or
        user.groups.filter(name='Cajero').exists()
    ))


def autorizar(user):
    if not puede_operar(user):
        raise PermissionDenied('Necesitás el rol Cajero para operar una caja.')


def importe(value, positivo=False):
    try:
        value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError('Monto inválido.')
    if not value.is_finite() or value < 0 or value > MAXIMO:
        raise ValidationError('El monto debe ser finito, no negativo y estar dentro del límite.')
    if value != value.quantize(Decimal('0.01')) or (positivo and value == 0):
        raise ValidationError('Usá hasta dos decimales y un monto mayor que cero para movimientos.')
    return value


def bloquear_caja(user, caja_id):
    autorizar(user)
    try:
        caja = Caja.objects.select_for_update().get(pk=caja_id, cajero=user)
    except Caja.DoesNotExist:
        raise PermissionDenied('No podés operar la caja de otro cajero.')
    if caja.cierre is not None:
        raise ValidationError('La caja está cerrada.')
    if not caja.habilitada:
        raise ValidationError('Debés contar y aceptar los fondos asignados antes de operar.')
    return caja


@transaction.atomic
def abrir_caja(user, cajero, montos, observacion=''):
    autorizar_admin(user)
    cajero = get_user_model().objects.select_for_update().get(pk=cajero.pk)
    if not es_cajero(cajero):
        raise ValidationError('Seleccioná un usuario activo con rol Cajero.')
    # El usuario asignado ya está bloqueado para evitar aperturas simultáneas.
    if Caja.objects.filter(cajero=cajero, cierre__isnull=True).exists():
        raise ValidationError('Ese cajero ya tiene una caja abierta o pendiente de aceptación.')
    monedas = list(Moneda.objects.filter(activa=True).order_by('pk'))
    if not monedas:
        raise ValidationError('No hay monedas activas.')
    if set(montos) != {m.pk for m in monedas}:
        raise ValidationError('Las monedas cambiaron. Recargá el formulario.')
    valores = {k: importe(v) for k, v in montos.items()}
    caja = Caja.objects.create(cajero=cajero, abierta_por=user, observacion_apertura=observacion)
    SaldoCaja.objects.bulk_create([SaldoCaja(caja=caja, moneda=m, inicial=valores[m.pk], actual=valores[m.pk]) for m in monedas])
    return caja


@transaction.atomic
def registrar_movimiento(user, caja_id, moneda_id, tipo, monto, concepto, clave, referencia=''):
    caja = bloquear_caja(user, caja_id)
    monto = importe(monto, positivo=True)
    concepto = concepto.strip()
    referencia = referencia.strip()
    if tipo not in dict(MovimientoCaja.TIPOS) or not concepto or len(concepto) > 255 or len(referencia) > 100:
        raise ValidationError('Tipo, concepto o referencia inválidos.')
    anterior = MovimientoCaja.objects.filter(clave=clave).first()
    if anterior:
        if (anterior.caja_id, anterior.moneda_id, anterior.tipo, anterior.monto, anterior.concepto, anterior.referencia) != (caja.pk, moneda_id, tipo, monto, concepto, referencia):
            raise ValidationError('Esta solicitud ya se usó para otro movimiento.')
        return anterior
    try:
        saldo = SaldoCaja.objects.select_for_update().get(caja=caja, moneda_id=moneda_id)
    except SaldoCaja.DoesNotExist:
        raise ValidationError('La moneda no pertenece a esta apertura de caja.')
    nuevo = saldo.actual + (monto if tipo == MovimientoCaja.INGRESO else -monto)
    saldo.actual = importe(nuevo)
    saldo.save(update_fields=['actual'])
    return MovimientoCaja.objects.create(caja=caja, moneda_id=moneda_id, tipo=tipo, monto=monto, concepto=concepto, referencia=referencia, clave=clave, creado_por=user)


@transaction.atomic
def anular_movimiento(user, movimiento_id, motivo):
    autorizar(user)
    movimiento = MovimientoCaja.objects.filter(pk=movimiento_id, caja__cajero=user).first()
    if movimiento is None:
        raise PermissionDenied('No podés anular ese movimiento.')
    caja = bloquear_caja(user, movimiento.caja_id)
    movimiento.refresh_from_db()
    if movimiento.cambio_id:
        return anular_cambio(user, movimiento.cambio_id, motivo)
    if movimiento.anulado_en is not None:
        raise ValidationError('El movimiento ya fue anulado.')
    motivo = motivo.strip()
    if not motivo:
        raise ValidationError('Indicá el motivo de anulación.')
    saldo = SaldoCaja.objects.select_for_update().get(caja=caja, moneda_id=movimiento.moneda_id)
    # Anular un ingreso exige que su importe todavía esté disponible.
    saldo.actual = importe(saldo.actual + (movimiento.monto if movimiento.tipo == MovimientoCaja.EGRESO else -movimiento.monto))
    saldo.save(update_fields=['actual'])
    movimiento.anulado_en = timezone.now()
    movimiento.anulado_por = user
    movimiento.motivo_anulacion = motivo
    movimiento.save(update_fields=['anulado_en', 'anulado_por', 'motivo_anulacion'])
    return movimiento


@transaction.atomic
def cerrar_caja(user, caja_id, montos, observacion=''):
    caja = bloquear_caja(user, caja_id)
    saldos = list(SaldoCaja.objects.select_for_update().filter(caja=caja))
    if set(montos) != {s.moneda_id for s in saldos}:
        raise ValidationError('Debés contar todas las monedas de la caja.')
    valores = {k: importe(v) for k, v in montos.items()}
    if any(valores[s.moneda_id] != s.actual for s in saldos) and not observacion.strip():
        raise ValidationError('Explicá las diferencias de arqueo en la observación.')
    for saldo in saldos:
        saldo.contado = valores[saldo.moneda_id]
        saldo.save(update_fields=['contado'])
    caja.cierre = timezone.now()
    caja.observacion_cierre = observacion
    caja.save(update_fields=['cierre', 'observacion_cierre'])
    return caja


from decimal import ROUND_HALF_UP, localcontext
from django.core import signing
from apps.divisas.models import TasaCambio

SALT_CAMBIO = 'cajas.cambio.v1'


def cotizar_cambio(moneda_recibida_id, moneda_entregada_id, monto):
    monto = importe(monto, positivo=True)
    monedas = {m.pk: m for m in Moneda.objects.filter(pk__in=[moneda_recibida_id, moneda_entregada_id], activa=True)}
    if len(monedas) != 2 or moneda_recibida_id not in monedas or moneda_entregada_id not in monedas:
        raise ValidationError('Seleccioná dos monedas activas diferentes.')
    recibida, entregada = monedas[moneda_recibida_id], monedas[moneda_entregada_id]
    if 'PYG' not in (recibida.codigo, entregada.codigo):
        raise ValidationError('Este formulario admite cambios entre PYG y una divisa extranjera.')
    divisa = entregada if recibida.codigo == 'PYG' else recibida
    cotizacion = TasaCambio.objects.filter(moneda=divisa).order_by('-fecha_actualizacion', '-pk').first()
    if cotizacion is None:
        raise ValidationError('La divisa no tiene una tasa configurada.')
    tipo = 'venta' if recibida.codigo == 'PYG' else 'compra'
    tasa = getattr(cotizacion, 'tasa_' + tipo)
    if not tasa.is_finite() or tasa <= 0:
        raise ValidationError('La tasa debe ser mayor que cero.')
    with localcontext() as ctx:
        ctx.prec = 40
        resultado = (monto / tasa if tipo == 'venta' else monto * tasa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    resultado = importe(resultado, positivo=True)
    return {
        'recibida': recibida, 'entregada': entregada, 'monto': monto,
        'resultado': resultado, 'tasa': tasa, 'tipo': tipo,
    }


def preparar_cambio(user, caja_id, recibida_id, entregada_id, monto, clave, referencia=''):
    autorizar(user)
    caja = Caja.objects.filter(pk=caja_id, cajero=user, cierre__isnull=True).first()
    if caja is None or not caja.habilitada:
        raise ValidationError('Necesitás tu caja aceptada y abierta para realizar el cambio.')
    c = cotizar_cambio(recibida_id, entregada_id, monto)
    payload = {
        'usuario': user.pk, 'caja': caja_id, 'recibida': recibida_id,
        'entregada': entregada_id, 'monto': str(c['monto']),
        'resultado': str(c['resultado']), 'tasa': str(c['tasa']),
        'tipo': c['tipo'], 'clave': str(clave), 'referencia': referencia.strip(),
    }
    return c, signing.dumps(payload, salt=SALT_CAMBIO)


@transaction.atomic
def confirmar_cambio(user, caja_id, token):
    try:
        d = signing.loads(token, salt=SALT_CAMBIO, max_age=600)
    except signing.BadSignature:
        raise ValidationError('La cotización venció o no es válida. Volvé a calcular.')
    if d['usuario'] != user.pk or d['caja'] != caja_id:
        raise PermissionDenied('La cotización no pertenece a tu caja.')
    caja = bloquear_caja(user, caja_id)
    anterior = CambioCaja.objects.filter(clave=d['clave']).first()
    if anterior:
        if (anterior.caja_id, anterior.moneda_recibida_id, anterior.moneda_entregada_id,
            anterior.monto_recibido, anterior.monto_entregado, anterior.tasa,
            anterior.tipo_tasa, anterior.referencia) != (
            caja_id, d['recibida'], d['entregada'], Decimal(d['monto']),
            Decimal(d['resultado']), Decimal(d['tasa']), d['tipo'], d['referencia']):
            raise ValidationError('La solicitud ya se utilizó para otro cambio.')
        return anterior
    c = cotizar_cambio(d['recibida'], d['entregada'], d['monto'])
    if c['tasa'] != Decimal(d['tasa']) or c['resultado'] != Decimal(d['resultado']) or c['tipo'] != d['tipo']:
        raise ValidationError('La tasa cambió. Volvé a calcular antes de confirmar.')
    saldos = {s.moneda_id: s for s in SaldoCaja.objects.select_for_update().filter(
        caja=caja, moneda_id__in=[d['recibida'], d['entregada']]).order_by('moneda_id')}
    if len(saldos) != 2:
        raise ValidationError('Ambas monedas deben estar incluidas en la apertura de caja.')
    entrada, salida = saldos[d['recibida']], saldos[d['entregada']]
    if salida.actual < c['resultado']:
        raise ValidationError('No hay suficiente efectivo en la moneda que debés entregar.')
    entrada.actual = importe(entrada.actual + c['monto'])
    salida.actual = importe(salida.actual - c['resultado'])
    entrada.save(update_fields=['actual'])
    salida.save(update_fields=['actual'])
    cambio = CambioCaja.objects.create(
        caja=caja, moneda_recibida=c['recibida'], moneda_entregada=c['entregada'],
        monto_recibido=c['monto'], monto_entregado=c['resultado'], tasa=c['tasa'],
        tipo_tasa=c['tipo'], clave=d['clave'], referencia=d['referencia'], creado_por=user)
    for moneda, tipo, monto in [(c['recibida'], 'ingreso', c['monto']), (c['entregada'], 'egreso', c['resultado'])]:
        MovimientoCaja.objects.create(caja=caja, cambio=cambio, moneda=moneda, tipo=tipo,
            monto=monto, concepto=f'Cambio #{cambio.pk}: {c["recibida"].codigo} a {c["entregada"].codigo}',
            referencia=d['referencia'], creado_por=user)
    return cambio


@transaction.atomic
def anular_cambio(user, cambio_id, motivo):
    autorizar(user)
    cambio = CambioCaja.objects.filter(pk=cambio_id, caja__cajero=user).first()
    if cambio is None:
        raise PermissionDenied('No podés anular este cambio.')
    caja = bloquear_caja(user, cambio.caja_id)
    cambio.refresh_from_db()
    if cambio.anulado_en:
        raise ValidationError('El cambio ya fue anulado.')
    motivo = motivo.strip()
    if not motivo or len(motivo) > 2000:
        raise ValidationError('Indicá un motivo de hasta 2000 caracteres.')
    saldos = {s.moneda_id: s for s in SaldoCaja.objects.select_for_update().filter(
        caja=caja, moneda_id__in=[cambio.moneda_recibida_id, cambio.moneda_entregada_id]).order_by('moneda_id')}
    entrada, salida = saldos[cambio.moneda_recibida_id], saldos[cambio.moneda_entregada_id]
    if entrada.actual < cambio.monto_recibido:
        raise ValidationError('No hay saldo suficiente para revertir el ingreso del cambio.')
    entrada.actual = importe(entrada.actual - cambio.monto_recibido)
    salida.actual = importe(salida.actual + cambio.monto_entregado)
    entrada.save(update_fields=['actual'])
    salida.save(update_fields=['actual'])
    cambio.anulado_en = timezone.now()
    cambio.anulado_por = user
    cambio.motivo_anulacion = motivo
    cambio.save(update_fields=['anulado_en', 'anulado_por', 'motivo_anulacion'])
    cambio.movimientos.update(anulado_en=cambio.anulado_en, anulado_por=user, motivo_anulacion=motivo)
    return cambio


@transaction.atomic
def aceptar_caja(user, caja_id, montos, observacion=''):
    autorizar(user)
    try:
        caja = Caja.objects.select_for_update().get(pk=caja_id, cajero=user)
    except Caja.DoesNotExist:
        raise PermissionDenied('Solo el cajero asignado puede aceptar esta caja.')
    if caja.cierre is not None:
        raise ValidationError('La caja está cerrada.')
    if caja.habilitada:
        raise ValidationError('La caja ya está habilitada. No se puede repetir la aceptación.')
    saldos = list(SaldoCaja.objects.select_for_update().filter(caja=caja).order_by('moneda_id'))
    if not saldos or set(montos) != {s.moneda_id for s in saldos}:
        raise ValidationError('Contá todas las monedas asignadas a la caja.')
    valores = {k: importe(v) for k, v in montos.items()}
    coincide = all(valores[s.moneda_id] == s.inicial for s in saldos)
    conteo = ConteoInicial.objects.create(caja=caja, cajero=user, coincide=coincide, observacion=observacion.strip())
    DetalleConteoInicial.objects.bulk_create([
        DetalleConteoInicial(conteo=conteo, moneda_id=s.moneda_id, asignado=s.inicial, contado=valores[s.moneda_id])
        for s in saldos
    ])
    if coincide:
        caja.aceptada_en = timezone.now()
        caja.aceptada_por = user
        caja.save(update_fields=['aceptada_en', 'aceptada_por'])
    # Si hay diferencia se conserva el intento, pero no se habilita ni modifica el saldo.
    return conteo
