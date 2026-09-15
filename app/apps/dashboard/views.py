# apps/dashboard/views.py
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout
from django.db.models import OuterRef, Subquery

from apps.divisas.models import Moneda, TasaCambio
from apps.users.client_selection import get_selected_client

PYG_CODE = 'PYG'


def get_currencies():
    latest_rate = TasaCambio.objects.filter(
        moneda=OuterRef('pk'),
    ).order_by('-fecha_actualizacion')
    return list(
        Moneda.objects.filter(activa=True)
        .annotate(
            compra=Subquery(latest_rate.values('tasa_compra')[:1]),
            venta=Subquery(latest_rate.values('tasa_venta')[:1]),
        )
        .filter(compra__isnull=False, venta__isnull=False)
        .order_by('codigo')
        .values('codigo', 'nombre', 'simbolo', 'compra', 'venta')
    )


def get_currency(code, currencies):
    return next((currency for currency in currencies if currency['codigo'] == code), None)


def format_money(value):
    return f"{value.quantize(Decimal('0.01')):,.2f}"


def calculate_conversion(amount, operation, currency):
    amount = Decimal(str(amount))
    rate = currency['venta'] if operation == 'compra' else currency['compra']

    return {
        'amount': amount,
        'operation': operation,
        'rate': rate,
        'foreign_currency': currency['codigo'],
        'from_currency': currency['codigo'],
        'to_currency': PYG_CODE,
        'result': amount * rate,
        'source_buy': currency['compra'],
        'source_sell': currency['venta'],
    }


def get_conversion_context(request):
    currencies = get_currencies()
    foreign_currencies = [currency for currency in currencies if currency['codigo'] != PYG_CODE]
    operation = request.POST.get('operation', 'compra')
    currency_code = request.POST.get(
        'currency',
        foreign_currencies[0]['codigo'] if foreign_currencies else '',
    )
    amount_value = request.POST.get('amount', '100')
    conversion = None
    error = None

    if request.method == 'POST':
        try:
            amount = Decimal(amount_value)
            if amount <= 0:
                error = 'El importe debe ser mayor a cero.'
            elif operation not in ('compra', 'venta'):
                error = 'Selecciona una operación válida.'
            else:
                currency = get_currency(currency_code, foreign_currencies)
                if currency is None:
                    error = 'Selecciona una divisa extranjera válida.'
                else:
                    conversion = calculate_conversion(amount, operation, currency)
        except (InvalidOperation, ValueError):
            error = 'Ingresa un importe válido para continuar.'

    return {
        'currencies': foreign_currencies,
        'foreign_currencies': foreign_currencies,
        'operation': operation,
        'currency': currency_code,
        'amount': amount_value,
        'conversion': conversion,
        'error': error,
    }


def home(request):
    es_analista = False
    cliente_activo = None

    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        cliente_activo = get_selected_client(request)
        if cliente_activo and not cliente_activo.activo:
            cliente_activo = None
        es_grupo_analista = request.user.groups.filter(name__icontains='analista').exists()
        es_usuario_analista = request.user.username.lower() in ['analista', 'analista cambiario']
        es_analista = (
            bool(profile and profile.role == 'Analista Cambiario')
            or es_grupo_analista
            or es_usuario_analista
            or request.user.is_superuser
        )

    context = {
        'user': request.user,
        'es_analista': es_analista,
        'cliente_activo': cliente_activo,
    }
    context.update(get_conversion_context(request))
    return render(request, 'dashboard.html', context)



def currency_converter(request):
    return render(
        request,
        'simulador/conversion.html',
        {'user': request.user, **get_conversion_context(request)},
    )


def custom_logout(request):
    django_logout(request)


    KEYCLOAK_URL = "http://localhost:8080/realms/global_exchange/protocol/openid-connect/logout"
    CLIENT_ID = "django_client"
    redirect_uri = request.build_absolute_uri('/')


    keycloak_logout_url = (
        f"{KEYCLOAK_URL}"
        f"?client_id={CLIENT_ID}"
        f"&post_logout_redirect_uri={redirect_uri}"
    )


    return redirect(keycloak_logout_url)