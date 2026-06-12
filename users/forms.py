from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario

class UsuarioCreationForm(forms.ModelForm):
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password_confirmation = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ('email', 'colegio', 'rol')

    def clean_password_confirmation(self):
        password = self.cleaned_data.get("password")
        password_confirmation = self.cleaned_data.get("password_confirmation")
        if password and password_confirmation and password != password_confirmation:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password_confirmation

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Encripta la clave correctamente
        if commit:
            user.save()
        return user

class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ('email', 'colegio', 'rol', 'is_active', 'is_staff')

class RegistroInscripcionForm(forms.Form):
    # DATOS DEL REPRESENTANTE
    cedula_rep = forms.CharField(label='Cédula Representante')
    nombre_rep = forms.CharField(label='Nombres')
    apellido_rep = forms.CharField(label='Apellidos')
    email_rep = forms.EmailField(label='Correo Electrónico')
    telefono_rep = forms.CharField(label='Teléfono') # <--- ESTO EVITA EL ERROR 1048
    parentesco = forms.ChoiceField(choices=[
        ('MADRE', 'Madre'), ('PADRE', 'Padre'), ('TUTOR', 'Tutor Legal')
    ])

    # DATOS DEL ESTUDIANTE
    cedula_est = forms.CharField(label='Cédula Escolar / ID')
    nombre_est = forms.CharField(label='Nombres Estudiante')
    apellido_est = forms.CharField(label='Apellidos Estudiante')
    fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    # DATOS ACADÉMICOS
    nivel = forms.ChoiceField(choices=[('INI', 'Inicial'), ('PRI', 'Primaria'), ('SEC', 'Secundaria')])
    seccion = forms.ModelChoiceField(queryset=None) # Se llena en el __init__
    monto_mensualidad = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        if colegio:
            # Filtra las secciones solo de ese colegio
            from academico.models import Seccion
            self.fields['seccion'].queryset = Seccion.objects.filter(colegio=colegio)