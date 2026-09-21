from django import forms

from .models import ConsultaPropiedad, SolicitudTasacion


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


class TasacionForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = SolicitudTasacion
        fields = ['nombre', 'email', 'telefono', 'direccion', 'tipo_propiedad', 'objetivo',
                  'metros_cubiertos', 'dormitorios', 'mensaje']
        labels = {
            'nombre': 'Tu nombre',
            'email': 'Tu email',
            'telefono': 'Tu teléfono o WhatsApp',
            'direccion': 'Dirección de la propiedad',
            'tipo_propiedad': 'Tipo de propiedad',
            'objetivo': '¿Qué querés hacer?',
            'metros_cubiertos': 'M² cubiertos (aprox.)',
            'dormitorios': 'Dormitorios',
            'mensaje': 'Algo más que quieras contarnos',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre y apellido'}),
            'email': forms.EmailInput(attrs={'placeholder': 'nombre@email.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Con código de área'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Calle, altura y localidad'}),
            'metros_cubiertos': forms.NumberInput(attrs={'placeholder': 'Ej: 120', 'min': 1}),
            'dormitorios': forms.NumberInput(attrs={'placeholder': 'Ej: 3', 'min': 0}),
            'mensaje': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Opcional'}),
        }

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if len(''.join(c for c in telefono if c.isdigit())) < 8:
            raise forms.ValidationError("Revisá el teléfono: tiene que tener al menos 8 números.")
        return telefono
