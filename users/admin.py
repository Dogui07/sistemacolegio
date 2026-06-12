from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol, Persona
from .forms import UsuarioCreationForm, UsuarioChangeForm 

@admin.register(Usuario)
class CustomUsuarioAdmin(UserAdmin):
    # Campos que se verán en la lista principal del admin
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm

    list_display = ('email', 'colegio', 'rol', 'is_staff')
    search_fields = ('email',)
    ordering = ('email',)

    # Vista de EDICIÓN de usuario (Quitamos username, añadimos colegio y rol)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Ubicación y Rol', {'fields': ('colegio', 'rol')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    # Vista de CREACIÓN de usuario (Lo que pide Django al darle "Añadir")
    # Es importante que el add_fieldsets coincida con tu modelo Custom
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # Incluimos los campos que el formulario necesita validar
            'fields': ('email', 'colegio', 'rol', 'password', 'password_confirmation'),
        }),
    )

# Registramos el modelo Persona
admin.site.register(Persona)

# Registramos el modelo de Roles
@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'colegio')
    list_filter = ('colegio',)