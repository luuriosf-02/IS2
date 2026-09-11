from apps.users.models import UserClientLink


def get_client_for_user(user):
    link = (
        UserClientLink.objects
        .select_related("client")
        .filter(
            user=user,
            status=UserClientLink.STATUS_APPROVED,
        )
        .first()
    )

    if link is None:
        return None

    return link.client