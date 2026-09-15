from apps.clientes.models import Cliente
from django.db.models import Q

from .models import UserClientLink


ACTIVE_CLIENT_SESSION_KEY = "active_client_id"


def get_available_clients(user):
    if not user.is_authenticated:
        return Cliente.objects.none()

    return Cliente.objects.filter(
        Q(
            user_links__user=user,
            user_links__status=UserClientLink.STATUS_APPROVED,
        )
        | Q(creado_por=user),
    ).distinct().order_by("nombre_razon_social")


def get_selected_client(request):
    clients = get_available_clients(request.user)
    selected_id = request.session.get(ACTIVE_CLIENT_SESSION_KEY)

    if selected_id is not None:
        selected_client = clients.filter(pk=selected_id).first()
        if selected_client is not None:
            return selected_client

    return clients.filter(activo=True).first() or clients.first()


def set_selected_client(request, client_id):
    client = get_available_clients(request.user).filter(pk=client_id).first()

    if client is None:
        return None

    request.session[ACTIVE_CLIENT_SESSION_KEY] = client.pk
    return client