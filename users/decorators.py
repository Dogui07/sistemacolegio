from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from colegios.models import Colegio  # Ajusta la importación según tu app de colegios

def permiso_finanzas_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, colegio_slug, *args, **kwargs):
        user = request.user

        # 1. Si ni siquiera está logueado, al login
        if not user.is_authenticated:
            return redirect('login')

        # 2. El Superusuario de Django tiene pase libre total
        if user.is_superuser:
            return view_func(request, colegio_slug, *args, **kwargs)

        # 3. Validar multi-colegio (Seguridad de inquilinos)
        colegio = get_object_or_404(Colegio, slug=colegio_slug)
        if user.colegio != colegio:
            messages.error(request, "No tienes autorización para acceder a esta institución.")
            return redirect('home')  # Cambia 'home' por tu ruta por defecto

        # 4. Validar tu permiso dinámico de Finanzas
        # Usamos 'if user.rol' porque en tu modelo permites que sea null/blank
        if user.rol and user.rol.can_manage_finances:
            return view_func(request, colegio_slug, *args, **kwargs)

        # 5. Si llegó aquí, está logueado pero no tiene el check de finanzas
        messages.error(request, "Tu rol no tiene permisos para gestionar cobros o pagos.")
        return redirect('home')

    return _wrapped_view