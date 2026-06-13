from django.db import models

# Usamos f-strings para que las rutas funcionen igual en Windows y Linux (Render)
def generar_ruta(instance, filename, tipo):
    slug = getattr(instance, 'slug', 'sin-slug')
    return f"assets/{slug}/images/{tipo}_{filename}"

def ruta_favicon_colegio(instance, filename): return generar_ruta(instance, filename, 'favicon')
def ruta_logo_colegio(instance, filename): return generar_ruta(instance, filename, 'logo')
def ruta_portada_colegio(instance, filename): return generar_ruta(instance, filename, 'portada')

class Colegio(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to=ruta_logo_colegio, null=True, blank=True)
    favicon = models.ImageField(upload_to=ruta_favicon_colegio, null=True, blank=True)
    imagen_portada = models.ImageField(upload_to=ruta_portada_colegio, null=True, blank=True)
    # Lema o frase corta impactante .
    lema = models.CharField(max_length=200, null=True, blank=True)
  
    # Colores principales para el diseño
    # Por defecto, colores "Madre Laura": Verde oscuro (#1a4731) y Oro (#c4a13d)
    color_principal = models.CharField(max_length=7, default="#1a4731") 
    color_secundario = models.CharField(max_length=7, default="#c4a13d")
    # Información de contacto básica
    direccion = models.CharField(max_length=300, null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    correo_contacto = models.EmailField(null=True, blank=True)
    
    imparte_inicial = models.BooleanField(default=False, verbose_name="Nivel Inicial")
    imparte_primaria = models.BooleanField(default=False, verbose_name="Nivel Primaria")
    imparte_secundaria = models.BooleanField(default=False, verbose_name="Nivel Secundaria")
    tiene_cantina = models.BooleanField(default=False, verbose_name="¿Tiene Módulo de Cantina?")

    def __str__(self):
        return self.nombre

class Publicacion(models.Model):
    TIPOS = [('EVENTO', 'Evento Próximo'), ('NOTICIA', 'Noticia/Blog')]
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='publicaciones')
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    
    imagen = models.ImageField(upload_to='publicaciones/', blank=True, null=True) 
    
    tipo = models.CharField(max_length=10, choices=TIPOS, default='NOTICIA')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_evento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - {self.colegio.nombre}"

class ImagenGaleria(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='imagenes')
    titulo = models.CharField(max_length=100, blank=True)
    imagen = models.ImageField(upload_to='galeria/', null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Imágenes de la Galería"

    def __str__(self):
        # Si tiene título, muestra el título, si no, un texto genérico con el nombre del colegio
        return self.titulo if self.titulo else f"Foto de {self.colegio.nombre}"

