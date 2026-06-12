"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Las rutas de usuarios deben ir ARRIBA de la del slug del colegio
    path('', include('users.urls')), 
    
    # 2. La ruta del colegio (que captura cualquier texto) va ABAJO
    path('', include('web.urls')),
     
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Sistema de Gestión de Colegios"
admin.site.site_title = "Portal Administrativo"
admin.site.index_title = "Bienvenido al Panel de Control"


# Servir archivos multimedia (fotos de alumnos, logos, blog) en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

