from django import forms

from apps.clientes.models import Cliente

from .models import UserClientLink
from .models import TasaCambio


class ClientLinkRequestForm(forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        clients_with_approved_links = UserClientLink.objects.filter(
            user=user,
            status=UserClientLink.STATUS_APPROVED,
        ).values_list(
            "client_id",
            flat=True,
        )

        available_clients = Cliente.objects.filter(
            creado_por=user,
        ).exclude(
            id__in=clients_with_approved_links,
        )

        self.available_clients = list(available_clients)
        self.client_rows = []
        for client in self.available_clients:
            selection_name = f"client_{client.pk}"
            status_name = f"tax_status_{client.pk}"
            self.fields[selection_name] = forms.BooleanField(
                required=False,
                label=client.nombre_razon_social,
            )
            self.fields[status_name] = forms.ChoiceField(
                required=False,
                choices=[
                    ("", "Selecciona una opción"),
                    ("true", "Contribuyente"),
                    ("false", "No contribuyente"),
                ],
                initial=(
                    "true" if client.es_contribuyente is True
                    else "false" if client.es_contribuyente is False
                    else ""
                ),
                disabled=client.es_contribuyente is not None,
                label="Condición tributaria",
                widget=forms.Select(attrs={"class": "form-select"}),
            )
            self.client_rows.append(
                {
                    "client": client,
                    "selection": self[selection_name],
                    "tax_status": self[status_name],
                }
            )

    def clean(self):
        cleaned_data = super().clean()
        selected_clients = []
        for client in self.available_clients:
            if not cleaned_data.get(f"client_{client.pk}"):
                continue
            selected_clients.append(client)
            if cleaned_data.get(f"tax_status_{client.pk}") not in ("true", "false"):
                self.add_error(
                    f"tax_status_{client.pk}",
                    "Indica si el cliente es contribuyente.",
                )

        if not selected_clients:
            raise forms.ValidationError("Selecciona al menos un cliente.")
        cleaned_data["selected_clients"] = selected_clients
        return cleaned_data

    @property
    def selected_clients(self):
        return self.cleaned_data.get("selected_clients", [])


class ReviewClientLinkForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ("approve", "Aprobar"),
            ("reject", "Rechazar"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-radio-group"}),
        label="Decisión",
    )

    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Indique el motivo del rechazo",
            }
        ),
        label="Motivo del rechazo",
    )

    categoria = forms.ChoiceField(
        choices=Cliente.CATEGORIA_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Categoría del cliente",
    )

    limite_credito = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }
        ),
        label="Límite de crédito",
    )

    def clean(self):
        cleaned_data = super().clean()

        action = cleaned_data.get("action")
        rejection_reason = cleaned_data.get(
            "rejection_reason",
            "",
        ).strip()

        if action == "reject" and not rejection_reason:
            self.add_error(
                "rejection_reason",
                "Debe indicar el motivo del rechazo.",
            )

        if action == "approve":
            if not cleaned_data.get("categoria"):
                self.add_error("categoria", "Debe asignar una categoría para aprobar.")
            if cleaned_data.get("limite_credito") is None:
                self.add_error("limite_credito", "Debe asignar un límite de crédito para aprobar.")

        return cleaned_data


class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['moneda_origen', 'moneda_destino', 'tasa_compra', 'tasa_venta']