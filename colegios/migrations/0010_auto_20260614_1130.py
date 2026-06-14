from django.db import migrations
from django.core.management import call_command

def cargar_datos(apps, schema_editor):
    # Esto busca el archivo data.json en la raíz del proyecto
    call_command('loaddata', 'data.json')

class Migration(migrations.Migration):

    dependencies = [
        # IMPORTANTE: Aquí debe ir el nombre del archivo de "merge" 
        # que se creó justo antes de este.
        ('colegios', '0009_merge_20260614_1130'), 
    ]

    operations = [
        migrations.RunPython(cargar_datos),
    ]