from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.db import transaction

from apps.clientes.models import Cliente
from .forms import ClientLinkRequestForm
from .forms import ReviewClientLinkForm
from .forms import TasaCambioForm
from .models import UserClientLink
from .models import TasaCambio
from .client_selection import get_available_clients, set_selected_client
from .services.keycloak_service import (
    assign_role_to_user,
    get_roles,
    get_users,
)


def assign_role(request):
    context = {}
    excluded_roles = {
        "Administrador",
        "default-roles-global_exchange",
        "offline_access",
        "uma_authorization",
    }

    try:
        users = get_users()
        roles = [
            role
            for role in get_roles()
            if role.get("name") not in excluded_roles
        ]

        context["users"] = users
        context["roles"] = roles

        if request.method == "POST":
            user_id = request.POST.get("user_id")
            role_name = request.POST.get("role_name")

            valid_role_names = {role.get("name") for role in roles}

            if not user_id or not role_name:
                context["error"] = (
                    "Debe seleccionar un usuario y un rol."
                )
            elif role_name not in valid_role_names:
                context["error"] = "El rol seleccionado no es válido."
            else:
                assign_role_to_user(
                    user_id,
                    role_name,
                )

                context["message"] = (
                    "Rol asignado correctamente."
                )

    except Exception as error:
        context["error"] = str(error)

    return render(
        request,
        "users/assign_role.html",
        context,
    )


@login_required
def request_client_link(request):
    if request.method == "POST":
        form = ClientLinkRequestForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            selected_clients = form.cleaned_data["clients"]

            for client in selected_clients:
                link, created = UserClientLink.objects.get_or_create(
                    user=request.user,
                    client=client,
                    defaults={
                        "status": UserClientLink.STATUS_PENDING,
                    },
                )

                if not created:
                    link.status = UserClientLink.STATUS_PENDING
                    link.reviewed_at = None
                    link.reviewed_by = None
                    link.rejection_reason = ""
                    link.save()

            messages.success(
                request,
                "La solicitud de vinculación fue enviada correctamente.",
            )

            return redirect("my_client_links")

    else:
        form = ClientLinkRequestForm(user=request.user)

    return render(
        request,
        "users/request_client_link.html",
        {
            "form": form,
        },
    )


@login_required
def activate_client(request):
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        action = request.POST.get("action", "activate")
        client = get_available_clients(request.user).filter(pk=client_id).first()

        if client is None:
            messages.error(
                request,
                "No puedes modificar ese cliente.",
            )
        elif action not in ("activate", "deactivate"):
            messages.error(request, "La acción solicitada no es válida.")
        elif action == "deactivate" and client.creado_por_id != request.user.id:
            messages.error(
                request,
                "Solo puedes modificar el estado de tus propios clientes.",
            )
        elif action == "deactivate":
            client.activo = False
            client.save(update_fields=["activo"])
            if request.session.get("active_client_id") == client.pk:
                request.session.pop("active_client_id", None)
            messages.success(request, f'Cliente desactivado: "{client.nombre_razon_social}".')
        elif client.creado_por_id == request.user.id and not client.activo and not client.activacion_permitida:
            messages.error(
                request,
                "La activación de ese cliente todavía no está permitida.",
            )
        elif client.creado_por_id == request.user.id:
            with transaction.atomic():
                Cliente.objects.filter(
                    creado_por=request.user,
                    activo=True,
                ).exclude(pk=client.pk).update(activo=False)
                client.activo = True
                client.save(update_fields=["activo"])
            set_selected_client(request, client.pk)
            messages.success(request, f'Cliente activo: "{client.nombre_razon_social}".')
        elif not client.activo:
            messages.error(request, "Ese cliente todavía no está activo.")
        else:
            set_selected_client(request, client.pk)
            messages.success(request, f'Cliente seleccionado: "{client.nombre_razon_social}".')

    return redirect(request.META.get("HTTP_REFERER") or "home")


@login_required
def my_client_links(request):
    links = UserClientLink.objects.filter(
        user=request.user,
        client__creado_por=request.user,
    ).select_related("client")

    return render(
        request,
        "users/my_client_links.html",
        {
            "links": links,
        },
    )


def can_review_client_links(user):
    if not user.is_authenticated:
        return False

    if user.is_staff or user.is_superuser:
        return True

    return getattr(
        getattr(user, "profile", None),
        "role",
        None,
    ) == "Administrador"


@login_required
def pending_client_links(request):
    if not can_review_client_links(request.user):
        raise PermissionDenied

    links = UserClientLink.objects.filter(
        status=UserClientLink.STATUS_PENDING,
    ).select_related(
        "user",
        "client",
    )

    return render(
        request,
        "users/pending_client_links.html",
        {
            "links": links,
        },
    )


@login_required
def review_client_link(request, link_id):
    if not can_review_client_links(request.user):
        raise PermissionDenied

    link = get_object_or_404(
        UserClientLink.objects.select_related(
            "user",
            "client",
        ),
        id=link_id,
    )

    if request.method == "POST":
        form = ReviewClientLinkForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data["action"]

            if action == "approve":
                link.status = UserClientLink.STATUS_APPROVED
                link.rejection_reason = ""
                link.client.activacion_permitida = True
                link.client.activo = False
                link.client.categoria = form.cleaned_data["categoria"]
                link.client.limite_credito = form.cleaned_data["limite_credito"]
                link.client.save(
                    update_fields=[
                        "activacion_permitida",
                        "activo",
                        "categoria",
                        "limite_credito",
                    ]
                )

                success_message = (
                    "La vinculación fue aprobada correctamente."
                )

            else:
                link.status = UserClientLink.STATUS_REJECTED
                link.rejection_reason = form.cleaned_data[
                    "rejection_reason"
                ]

                success_message = (
                    "La vinculación fue rechazada correctamente."
                )

            link.reviewed_at = timezone.now()
            link.reviewed_by = request.user
            link.save()

            messages.success(request, success_message)

            return redirect("pending_client_links")

    else:
        form = ReviewClientLinkForm()

    return render(
        request,
        "users/review_client_link.html",
        {
            "link": link,
            "form": form,
        },
        
    )
@login_required
def gestion_divisas_view(request):
    # Verificación de Rol por nombre exacto de Keycloak
    es_analista = request.user.groups.filter(name='Analista Cambiario').exists()
    
    if not es_analista and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    tasas = TasaCambio.objects.all()

    if request.method == 'POST':
        form = TasaCambioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tasa de cambio actualizada correctamente.')
            return redirect('gestion_divisas')
    else:
        form = TasaCambioForm()

    return render(request, 'divisas/gestion_tasas.html', {
        'form': form,
        'tasas': tasas
    })