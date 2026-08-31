import requests

KEYCLOAK_URL = "http://keycloak:8080"
REALM = "global_exchange"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password"


def get_admin_token():
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"

    data = {
        "client_id": "admin-cli",
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "grant_type": "password",
    }

    response = requests.post(url, data=data)
    response.raise_for_status()

    return response.json()["access_token"]


def get_users():
    token = get_admin_token()

    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def get_roles():
    token = get_admin_token()

    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def get_role_by_name(role_name):
    token = get_admin_token()

    url = (
        f"{KEYCLOAK_URL}/admin/realms/"
        f"{REALM}/roles/{role_name}"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def assign_role_to_user(user_id, role_name):
    token = get_admin_token()

    role = get_role_by_name(role_name)

    url = (
        f"{KEYCLOAK_URL}/admin/realms/"
        f"{REALM}/users/{user_id}/role-mappings/realm"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    role_data = [
        {
            "id": role["id"],
            "name": role["name"],
        }
    ]

    response = requests.post(
        url,
        headers=headers,
        json=role_data
    )

    response.raise_for_status()

    return True