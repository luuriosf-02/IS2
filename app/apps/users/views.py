from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone

from .forms import ClientLinkRequestForm
from .forms import ReviewClientLinkForm
from .models import UserClientLink
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
                link.client.save(
                    update_fields=["activacion_permitida", "activo"]
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