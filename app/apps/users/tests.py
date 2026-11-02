from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
import time

from apps.clientes.models import Cliente

from .forms import ClientLinkRequestForm
from .models import UserClientLink


class ClientLinkTaxStatusTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="link-tax-status",
            password="test-password",
        )
        self.client_one = Cliente.objects.create(
            nombre_razon_social="Cliente individual",
            documento="1234567",
            creado_por=self.user,
        )
        self.client_two = Cliente.objects.create(
            nombre_razon_social="Cliente empresa",
            documento="800022475",
            tipo_persona="JURIDICA",
            creado_por=self.user,
        )

    def test_request_form_accepts_separate_tax_status_per_client(self):
        form = ClientLinkRequestForm(
            {
                f"client_{self.client_one.pk}": "on",
                f"tax_status_{self.client_one.pk}": "false",
                f"client_{self.client_two.pk}": "on",
                f"tax_status_{self.client_two.pk}": "true",
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            [client.pk for client in form.selected_clients],
            [self.client_one.pk, self.client_two.pk],
        )

    def test_tax_status_is_disabled_after_first_request_value(self):
        self.client_one.es_contribuyente = False
        self.client_one.save(update_fields=["es_contribuyente"])

        form = ClientLinkRequestForm(
            {
                f"client_{self.client_one.pk}": "on",
                f"tax_status_{self.client_one.pk}": "true",
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.fields[f"tax_status_{self.client_one.pk}"].disabled)
        self.assertEqual(
            form.cleaned_data[f"tax_status_{self.client_one.pk}"],
            "false",
        )

    def test_saved_tax_status_cannot_be_changed(self):
        self.client_one.es_contribuyente = True
        self.client_one.save(update_fields=["es_contribuyente"])

        self.client_one.es_contribuyente = False
        with self.assertRaises(ValidationError):
            self.client_one.save(update_fields=["es_contribuyente"])

    def test_request_persists_tax_status_and_creates_pending_link(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()

        response = self.client.post(
            reverse("request_client_link"),
            {
                f"client_{self.client_one.pk}": "on",
                f"tax_status_{self.client_one.pk}": "false",
            },
        )

        self.assertRedirects(response, reverse("my_client_links"))
        self.client_one.refresh_from_db()
        self.assertIs(self.client_one.es_contribuyente, False)
        self.assertTrue(
            UserClientLink.objects.filter(
                user=self.user,
                client=self.client_one,
                status=UserClientLink.STATUS_PENDING,
            ).exists()
        )

    def test_request_page_shows_tax_status_for_each_client(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()

        response = self.client.get(reverse("request_client_link"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Condición tributaria")
        self.assertContains(response, "Cliente individual")
        self.assertContains(response, "Cliente empresa")