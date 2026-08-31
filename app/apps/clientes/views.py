from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Cliente

@login_required(login_url='oidc_authentication_request_view')
def lista_clientes(request):
    """Vista para listar todos los clientes registrados."""
    clientes = Cliente.objects.all().order_by('-fecha_creacion')
    context = {
        'clientes': clientes,
    }
    return render(request, 'clientes/lista_clientes.html', context)

@login_required(login_url='oidc_authentication_request_view')
def detalle_cliente(request, pk):
    """Vista para ver el detalle de un cliente específico."""
    cliente = Cliente.objects.get(pk=pk)
    context = {
        'cliente': cliente,
    }
    return render(request, 'clientes/detalle_cliente.html', context)
