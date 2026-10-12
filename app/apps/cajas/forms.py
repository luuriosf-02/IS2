import uuid
from decimal import Decimal
from django import forms
from apps.divisas.models import Moneda
from .models import MovimientoCaja


class ConteoForm(forms.Form):
    observacion = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, caja=None, **kwargs):
        super().__init__(*args, **kwargs)
        if caja:
            self.monedas = [s.moneda for s in caja.saldos.select_related('moneda').all()]
        else:
            self.monedas = list(Moneda.objects.filter(activa=True).order_by('codigo'))
        for moneda in self.monedas:
            self.fields[f'moneda_{moneda.pk}'] = forms.DecimalField(label=f'{moneda.nombre} ({moneda.codigo})', min_value=0, max_digits=18, decimal_places=2, initial=0)

    def montos(self):
        return {m.pk: self.cleaned_data[f'moneda_{m.pk}'] for m in self.monedas}


class MovimientoForm(forms.Form):
    moneda = forms.ModelChoiceField(queryset=Moneda.objects.none())
    tipo = forms.ChoiceField(choices=MovimientoCaja.TIPOS)
    monto = forms.DecimalField(min_value=Decimal('0.01'), max_digits=18, decimal_places=2)
    concepto = forms.CharField(max_length=255)
    referencia = forms.CharField(max_length=100, required=False)
    clave = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, caja, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['moneda'].queryset = Moneda.objects.filter(pk__in=caja.saldos.values('moneda_id')).order_by('codigo')
        self.fields['clave'].initial = uuid.uuid4()


class AnulacionForm(forms.Form):
    motivo = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={'rows': 3}))
