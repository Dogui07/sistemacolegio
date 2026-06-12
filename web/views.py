from django.shortcuts import render, get_object_or_404
from colegios.models import Colegio

def index(request, colegio_slug):
    # Buscamos el colegio por su slug
    colegio = get_object_or_404(Colegio, slug=colegio_slug)
    
    # Pasamos el objeto 'colegio' al template
    # Gracias a las 'related_name' que pusimos en los modelos, 
    # el template podrá acceder a colegio.publicaciones y colegio.imagenes directamente.
    return render(request, 'web/index.html', {
        'colegio': colegio,
    })
