from django.contrib import admin
from .models import Colegio, Publicacion, ImagenGaleria #,AnioEscolar, Seccion, Grado 

class ImagenGaleriaInline(admin.TabularInline): # Para mostrar las imágenes de galería dentro del admin del Colegio
    model = ImagenGaleria
    extra = 3  # Esto muestra 3 espacios vacíos para subir fotos nuevas de una vez
    fields = ('titulo', 'imagen')

# Registro del Colegio
@admin.register(Colegio) 
class ColegioAdmin(admin.ModelAdmin):
    # He limpiado las líneas duplicadas aquí
    list_display = ('nombre', 'imparte_inicial', 'imparte_primaria', 'imparte_secundaria', 'tiene_cantina')
    list_editable = ('imparte_inicial', 'imparte_primaria', 'imparte_secundaria', 'tiene_cantina')
    
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [ImagenGaleriaInline]

    fieldsets = (
        (None, {
            # AQUÍ HEMOS AGREGADO 'favicon'
            'fields': ('nombre', 'slug', 'logo', 'favicon', 'color_principal', 'imagen_portada')
        }),
        ('Niveles Educativos', {
            'fields': ('imparte_inicial', 'imparte_primaria', 'imparte_secundaria'),
            'description': 'Seleccione los niveles que imparte esta institución.'
        }),
        ('Módulos Especiales', {
            'fields': ('tiene_cantina',),
            'description': 'Active los módulos adicionales contratados por la institución.'
        }),
    )

# Registro de las Publicaciones (Blog/Eventos)
@admin.register(Publicacion) # Decorador para registrar el modelo Publicacion con su configuración personalizada
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'colegio', 'tipo', 'fecha_creacion')
    list_filter = ('colegio', 'tipo')
    search_fields = ('titulo', 'contenido')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Los administradores de colegio solo ven sus propias publicaciones
        return qs.filter(colegio=request.user.colegio)

    def save_model(self, request, obj, form, change):
        # Si no es superusuario, le asignamos su colegio automáticamente al guardar
        if not request.user.is_superuser:
            obj.colegio = request.user.colegio
        super().save_model(request, obj, form, change)


@admin.register(ImagenGaleria) # Decorador para registrar el modelo ImagenGaleria con su configuración personalizada
class ImagenGaleriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'colegio', 'fecha_subida')
    list_filter = ('colegio',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(colegio=request.user.colegio)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.colegio = request.user.colegio
        super().save_model(request, obj, form, change)





