from datetime import date

from django import forms

from .models import MedioPago


class MedioPagoForm(forms.ModelForm):
    class Meta:
        model = MedioPago

        fields = [
            "tipo",
            "alias",
            "titular",
            "marca",
            "ultimos_cuatro",
            "mes_vencimiento",
            "anio_vencimiento",
            "predeterminado",
            "activo",
        ]

        widgets = {
            "tipo": forms.Select(
                attrs={"class": "form-control"}
            ),
            "alias": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "titular": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "marca": forms.Select(
                attrs={"class": "form-control"}
            ),
            "ultimos_cuatro": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": "4",
                    "inputmode": "numeric",
                }
            ),
            "mes_vencimiento": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "12",
                }
            ),
            "anio_vencimiento": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": str(date.today().year),
                }
            ),
        }

    def clean_ultimos_cuatro(self):
        valor = self.cleaned_data["ultimos_cuatro"]

        if not valor.isdigit() or len(valor) != 4:
            raise forms.ValidationError(
                "Debe ingresar exactamente cuatro números."
            )

        return valor

    def clean(self):
        cleaned_data = super().clean()

        mes = cleaned_data.get("mes_vencimiento")
        anio = cleaned_data.get("anio_vencimiento")

        if mes is None or anio is None:
            return cleaned_data

        hoy = date.today()

        if anio < hoy.year or (
            anio == hoy.year and mes < hoy.month
        ):
            self.add_error(
                "anio_vencimiento",
                "El medio de pago está vencido.",
            )

        return cleaned_data