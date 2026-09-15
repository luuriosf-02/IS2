from .client_selection import get_available_clients, get_selected_client


def active_client(request):
    if not request.user.is_authenticated:
        return {
            "available_clients": [],
            "selected_client": None,
        }

    return {
        "available_clients": get_available_clients(request.user),
        "selected_client": get_selected_client(request),
    }