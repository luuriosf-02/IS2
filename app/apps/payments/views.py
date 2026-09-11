from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.users.models import UserClientLink

from .forms import MedioPagoForm
from .models import MedioPago


def obtener_cliente_del_usuario(user):
    """
    Obtiene el cliente vinculado y aprobado del usuario autenticado.
    """

    vinculacion = (
        UserClientLink.objects
        .select_related("client")
        .filter(
            user=user,
            status=UserClientLink.STATUS_APPROVED,
        )
        .first()
    )

    if vinculacion is None:
        raise PermissionDenied(
            "No tiene una vinculación aprobada con un cliente."
        )

    return vinculacion.client


@login_required
def lista_medios_pago(request):
    """
    Muestra los medios de pago del cliente vinculado al usuario.

    Args:
        request: Solicitud HTTP del usuario autenticado.

    Returns:
        HttpResponse: Página con la lista de medios de pago.

    Raises:
        PermissionDenied: Si el usuario no posee una vinculación
        aprobada con un cliente.
    """
    cliente = obtener_cliente_del_usuario(request.user)

    medios_pago = MedioPago.objects.filter(
        cliente=cliente
    )

    return render(
        request,
        "payments/lista.html",
        {
            "cliente": cliente,
            "medios_pago": medios_pago,
        },
    )


@login_required
def crear_medio_pago(request):
    cliente = obtener_cliente_del_usuario(request.user)

    if request.method == "POST":
        form = MedioPagoForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                medio_pago = form.save(commit=False)
                medio_pago.cliente = cliente

                if medio_pago.predeterminado:
                    MedioPago.objects.filter(
                        cliente=cliente,
                        predeterminado=True,
                    ).update(
                        predeterminado=False
                    )

                medio_pago.save()

            messages.success(
                request,
                "El medio de pago fue registrado correctamente.",
            )

            return redirect("payments:lista")

    else:
        form = MedioPagoForm()

    return render(
        request,
        "payments/formulario.html",
        {
            "form": form,
            "titulo": "Registrar medio de pago",
            "texto_boton": "Guardar medio de pago",
        },
    )


@login_required
def editar_medio_pago(request, pk):
    cliente = obtener_cliente_del_usuario(request.user)

    medio_pago = get_object_or_404(
        MedioPago,
        pk=pk,
        cliente=cliente,
    )

    if request.method == "POST":
        form = MedioPagoForm(
            request.POST,
            instance=medio_pago,
        )

        if form.is_valid():
            with transaction.atomic():
                medio_pago = form.save(commit=False)

                if medio_pago.predeterminado:
                    MedioPago.objects.filter(
                        cliente=cliente,
                        predeterminado=True,
                    ).exclude(
                        pk=medio_pago.pk
                    ).update(predeterminado=False)

                medio_pago.save()

            messages.success(
                request,
                "El medio de pago fue actualizado correctamente.",
            )

            return redirect("payments:lista")
    else:
        form = MedioPagoForm(instance=medio_pago)

    return render(
        request,
        "payments/formulario.html",
        {
            "form": form,
            "medio_pago": medio_pago,
            "titulo": "Editar medio de pago",
            "texto_boton": "Guardar cambios",
        },
    )


@login_required
def eliminar_medio_pago(request, pk):
    cliente = obtener_cliente_del_usuario(request.user)

    medio_pago = get_object_or_404(
        MedioPago,
        pk=pk,
        cliente=cliente,
    )

    if request.method == "POST":
        medio_pago.delete()

        messages.success(
            request,
            "El medio de pago fue eliminado correctamente.",
        )

        return redirect("payments:lista")

    return render(
        request,
        "payments/confirmar_eliminacion.html",
        {
            "medio_pago": medio_pago,
        },
    )