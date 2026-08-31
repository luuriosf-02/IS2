from django.urls import path

from .views import assign_role
from .views import my_client_links
from .views import pending_client_links
from .views import request_client_link
from .views import review_client_link


urlpatterns = [
    path(
        "assign-role/",
        assign_role,
        name="assign_role",
    ),
    path(
        "client-links/request/",
        request_client_link,
        name="request_client_link",
    ),
    path(
        "client-links/mine/",
        my_client_links,
        name="my_client_links",
    ),
    path(
        "client-links/pending/",
        pending_client_links,
        name="pending_client_links",
    ),
    path(
        "client-links/<int:link_id>/review/",
        review_client_link,
        name="review_client_link",
    ),
]