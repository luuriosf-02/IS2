# apps/dashboard/views.py
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout

CURRENCIES = [
    {"code": "USD", "name": "Dólar estadounidense", "compra": Decimal("0.96"), "venta": Decimal("1.00")},
    {"code": "EUR", "name": "Euro", "compra": Decimal("0.90"), "venta": Decimal("0.94")},
    {"code": "GBP", "name": "Libra esterlina", "compra": Decimal("0.81"), "venta": Decimal("0.85")},
    {"code": "CLP", "name": "Peso chileno", "compra": Decimal("930.00"), "venta": Decimal("970.00")},
    {"code": "ARS", "name": "Peso argentino", "compra": Decimal("920.00"), "venta": Decimal("980.00")},
]


def get_currency(code):
    for currency in CURRENCIES:
        if currency["code"] == code:
            return currency
    return CURRENCIES[0]


def format_money(value):
    return f"{value.quantize(Decimal('0.01')):,.2f}"


def calculate_conversion(amount, from_currency, to_currency):
    amount = Decimal(str(amount))
    source = get_currency(from_currency)
    target = get_currency(to_currency)

    if source["code"] == target["code"]:
        return {
            "amount": amount,
            "result": amount,
            "from_currency": source["code"],
            "to_currency": target["code"],
            "source_sell": source["venta"],
            "target_buy": target["compra"],
            "source_buy": source["compra"],
            "target_sell": target["venta"],
        }

    usd_value = amount / source["venta"]
    converted = usd_value * target["compra"]

    return {
        "amount": amount,
        "result": converted,
        "from_currency": source["code"],
        "to_currency": target["code"],
        "source_sell": source["venta"],
        "target_buy": target["compra"],
        "source_buy": source["compra"],
        "target_sell": target["venta"],
    }


def home(request):
    es_analista = False

    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        es_grupo_analista = request.user.groups.filter(name__icontains='analista').exists()
        es_usuario_analista = request.user.username.lower() in ['analista', 'analista cambiario']
        es_analista = (
            bool(profile and profile.role == 'Analista Cambiario')
            or es_grupo_analista
            or es_usuario_analista
            or request.user.is_superuser
        )

    return render(request, 'dashboard.html', {
        'user': request.user,
        'es_analista': es_analista,
    })



def currency_converter(request):
    from_currency = request.POST.get('from_currency', 'USD')
    to_currency = request.POST.get('to_currency', 'EUR')
    amount_value = request.POST.get('amount', '100')
    conversion = None
    error = None

    if request.method == 'POST':
        try:
            amount = Decimal(amount_value)
            if amount <= 0:
                error = 'El importe debe ser mayor a cero.'
            else:
                conversion = calculate_conversion(amount, from_currency, to_currency)
        except (InvalidOperation, ValueError):
            error = 'Ingresa un importe válido para continuar.'

    return render(
        request,
        'simulador/conversion.html',
        {
            'user': request.user,
            'currencies': CURRENCIES,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount': amount_value,
            'conversion': conversion,
            'error': error,
        },
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