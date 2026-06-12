# academico/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import BilleteraCantina
from .models import Inscripcion, Seccion, Asignatura, CargaAcademica

@receiver(post_save, sender=Seccion)
def poblar_carga_academica(sender, instance, created, **kwargs):
    """
    Escucha la creación de secciones en la app 'academico'.
    Busca las asignaturas correspondientes del catálogo y genera la carga académica.
    """
    if created:
        # Buscamos las asignaturas que coinciden con la nueva sección
        asignaturas_coincidentes = Asignatura.objects.filter(
            colegio=instance.colegio,
            nivel=instance.nivel,
            grado=instance.grado
        )
        
        # Estructuramos el bloque de registros para la inserción masiva
        nuevos_registros_carga = [
            CargaAcademica(seccion=instance, asignatura=asignatura)
            for asignatura in asignaturas_coincidentes
        ]
        
        # Guardamos todo de un solo golpe si hay coincidencias
        if nuevos_registros_carga:
            CargaAcademica.objects.bulk_create(nuevos_registros_carga)

@receiver(post_save, sender=Inscripcion)
def crear_billetera_automatica(sender, instance, created, **kwargs):
    """
    Se ejecuta tras registrar o activar una inscripción del estudiante.
    Garantiza que el alumno tenga su cuenta de prepago lista en 0.00 BS.
    """
    # Si la inscripción se está creando y su estado inicial es ACTIVO
    if created and instance.estado == 'ACTIVO':
        BilleteraCantina.objects.get_or_create(
            estudiante=instance.estudiante,
            defaults={'saldo': 0.00}
        )