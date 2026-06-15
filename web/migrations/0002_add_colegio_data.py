from django.db import migrations

def crear_colegio_inicial(apps, schema_editor):
    # ¡IMPORTANTE! Cambia 'web' por 'colegios' aquí
    Colegio = apps.get_model('colegios', 'Colegio') 

    if not Colegio.objects.filter(slug='Colegio-Madre-Laura').exists():
        Colegio.objects.create(
            nombre="Colegio Madre Laura",
            slug="Colegio-Madre-Laura",
        )

class Migration(migrations.Migration):
    # Asegúrate de que aquí también coincida con el nombre del archivo de la migración anterior
    # Si tu archivo se llama 0001_initial.py dentro de la carpeta 'colegios', debería ser ('colegios', '0001_initial')
    dependencies = [
        ('colegios', '0001_initial'), 
    ]

    operations = [
        migrations.RunPython(crear_colegio_inicial),
    ]