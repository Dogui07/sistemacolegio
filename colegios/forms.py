from django import forms # Importamos el módulo de formularios de Django
from .models import Publicacion # Importamos el modelo Publicacion desde el archivo models.py del mismo directorio

# Creamos un pequeño widget personalizado que admita múltiples archivos
class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

# Creamos el campo personalizado para usar ese widget
class MultipleFileField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class PublicacionForm(forms.ModelForm): #
    class Meta: # Definimos la clase Meta para especificar el modelo y los campos que se incluirán en el formulario
        model = Publicacion # Especificamos que el formulario se basa en el modelo Publicacion
        fields = ['titulo', 'contenido', 'tipo', 'imagen'] # Especificamos los campos que se incluirán en el formulario
        widgets = { # Personalizamos los widgets para cada campo del formulario
            'titulo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none',
                'placeholder': 'Ej: Gran Bingo Familiar'
            }),  
            'contenido': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none',
                'rows': 4,
                'placeholder': 'Escribe aquí los detalles de la noticia...'
            }),
            'tipo': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),

        }

class GaleriaForm(forms.Form):
    # 3. Usamos nuestro nuevo campo aquí
    fotos = MultipleFileField(widget=MultipleFileInput(attrs={
        'multiple': True,
        'class': 'w-full px-4 py-8 border-2 border-dashed border-gray-300 rounded-2xl text-center cursor-pointer hover:border-blue-500 transition-colors'
    }))
