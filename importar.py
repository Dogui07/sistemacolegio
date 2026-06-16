import os
import django
from django.db.models.signals import post_save

# Configura tu entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# IMPORTA TU SEÑAL AQUÍ
# Ajusta la ruta según donde esté definida tu función
from academico.signals import crear_billetera_automatica
from django.core.management import call_command

# 1. Desconecta la señal antes de importar
post_save.disconnect(crear_billetera_automatica, sender='academico.Inscripcion')

print("Señal desconectada. Iniciando carga de datos...")

# 2. Carga los datos
call_command('loaddata', 'data.json')

print("¡Carga finalizada con éxito!")