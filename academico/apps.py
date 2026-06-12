# academico/apps.py
from django.apps import AppConfig

class AcademicoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academico'  # Nombre de tu aplicación de modelos

    def ready(self):
        # Con esto Django carga las señales de la app académico al iniciar el servidor
        import academico.signals
