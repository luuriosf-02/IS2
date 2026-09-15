from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    """Formulario para crear y editar clientes."""

    def __init__(self, *args, permitir_activacion=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['activo'].disabled = not permitir_activacion
        if not self.instance.pk:
            self.fields['activo'].initial = False
    
    class Meta:
        model = Cliente
        fields = ['nombre_razon_social', 'documento', 'tipo_persona', 'activo']
        widgets = {
            'nombre_razon_social': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Juan Pérez o Empresa S.A.',
                'required': True,
            }),
            'documento': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: 12345678 o RUC-123456-1',
                'required': True,
            }),
            'tipo_persona': forms.Select(attrs={
                'class': 'form-select',
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }
        labels = {
            'nombre_razon_social': 'Nombre o Razón Social *',
            'documento': 'RUC o CI *',
            'tipo_persona': 'Tipo de Persona *',
            'activo': 'Cliente Activo',
        }
        help_texts = {
            'documento': 'El documento debe ser único en el sistema',
            'activo': 'Marcar si el cliente está activo',
        }

    def clean_documento(self):
        """Validar que el documento sea único."""
        documento = self.cleaned_data.get('documento')
        # Si estamos editando (self.instance.pk existe), excluir el cliente actual
        if self.instance.pk:
            if Cliente.objects.filter(documento=documento).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Este documento ya está registrado en el sistema.')
        else:
            if Cliente.objects.filter(documento=documento).exists():
                raise forms.ValidationError('Este documento ya está registrado en el sistema.')
        return documento

