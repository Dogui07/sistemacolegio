
from django.db import migrations

def crear_colegio_inicial(apps, schema_editor):
    Colegio = apps.get_model('web', 'Colegio') # 'web' es el nombre de tu app, 'Colegio' el modelo

    # Verificamos si ya existe para no duplicarlo
    if not Colegio.objects.filter(slug='Colegio-Madre-Laura').exists():
        Colegio.objects.create(
            nombre="Colegio Madre Laura",
            slug="Colegio-Madre-Laura",
            # Puedes agregar otros campos aquí si los necesitas
        )

class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_colegio_inicial),
    ]