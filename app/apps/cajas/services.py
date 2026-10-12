"""Operaciones atómicas de efectivo. No confirman pagos electrónicos."""
from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from apps.divisas.models import Moneda
from .models import Caja, SaldoCaja, MovimientoCaja

MAXIMO = Decimal('9999999999999999.99')


def puede_operar(user):
    return bool(user.is_authenticated and user.is_active and (
        user.is_superuser or
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
    return caja


@transaction.atomic
def abrir_caja(user, montos, observacion=''):
    autorizar(user)
    # Bloqueo del usuario: también protege cuando todavía no existe una caja.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    if Caja.objects.filter(cajero=user, cierre__isnull=True).exists():
        raise ValidationError('Ya tenés una caja abierta.')
    monedas = list(Moneda.objects.filter(activa=True).order_by('pk'))
    if not monedas:
        raise ValidationError('No hay monedas activas.')
    if set(montos) != {m.pk for m in monedas}:
        raise ValidationError('Las monedas cambiaron. Recargá el formulario.')
    valores = {k: importe(v) for k, v in montos.items()}
    caja = Caja.objects.create(cajero=user, observacion_apertura=observacion)
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
