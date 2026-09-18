from django import forms

from .models import ConsultaPropiedad


class HoneypotMixin(forms.Form):
    """Campo trampa invisible para bots: un humano nunca lo completa."""
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def es_spam(self):
        return bool(self.cleaned_data.get('website'))


class ContactoForm(HoneypotMixin, forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Tu Nombre Completo'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Tu Correo Electrónico'})
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Tu Teléfono (Opcional)'})
    )
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Escribe tu consulta aquí...', 'rows': 4})
    )


class ConsultaPropiedadForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = ConsultaPropiedad
        fields = ['nombre', 'email', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Tu Nombre'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Tu Email'}),
            'mensaje': forms.Textarea(attrs={'placeholder': 'Mensaje...', 'rows': 4}),
        }