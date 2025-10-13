from django import forms

class ContactoForm(forms.Form):
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