from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Cliente
from .forms import ClienteForm

@login_required(login_url='oidc_authentication_request_view')
def lista_clientes(request):
    """Vista para listar los clientes creados por el usuario."""
    clientes = Cliente.objects.filter(
        creado_por=request.user,
    ).order_by('-fecha_creacion')
    context = {
        'clientes': clientes,
    }
    return render(request, 'clientes/lista_clientes.html', context)

@login_required(login_url='oidc_authentication_request_view')
def crear_cliente(request):
    """Vista para crear un nuevo cliente."""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            cliente.creado_por = request.user
            cliente.activo = False
            cliente.save(update_fields=['creado_por', 'activo'])
            messages.success(request, f'Cliente "{cliente.nombre_razon_social}" creado exitosamente.')
            return redirect('clientes:detalle', pk=cliente.pk)
    else:
        form = ClienteForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Cliente',
        'accion': 'Crear',
    }
    return render(request, 'clientes/form_cliente.html', context)

@login_required(login_url='oidc_authentication_request_view')
def editar_cliente(request, pk):
    """Vista para editar un cliente existente."""
    cliente = get_object_or_404(
        Cliente,
        pk=pk,
        creado_por=request.user,
    )
    
    if request.method == 'POST':
        form = ClienteForm(
            request.POST,
            instance=cliente,
            permitir_activacion=cliente.activacion_permitida,
        )
        if form.is_valid():
            with transaction.atomic():
                cliente = form.save(commit=False)
                if cliente.activo:
                    Cliente.objects.filter(
                        creado_por=request.user,
                        activo=True,
                    ).exclude(pk=cliente.pk).update(activo=False)
                cliente.save()
            messages.success(request, f'Cliente "{cliente.nombre_razon_social}" actualizado exitosamente.')
            return redirect('clientes:detalle', pk=cliente.pk)
    else:
        form = ClienteForm(
            instance=cliente,
            permitir_activacion=cliente.activacion_permitida,
        )
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo': f'Editar Cliente: {cliente.nombre_razon_social}',
        'accion': 'Actualizar',
    }
    return render(request, 'clientes/form_cliente.html', context)

@login_required(login_url='oidc_authentication_request_view')
def detalle_cliente(request, pk):
    """Vista para ver el detalle de un cliente específico."""
    cliente = get_object_or_404(
        Cliente,
        pk=pk,
        creado_por=request.user,
    )
    context = {
        'cliente': cliente,
    }
    return render(request, 'clientes/detalle_cliente.html', context)
