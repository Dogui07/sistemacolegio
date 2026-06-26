#academico/models.py
from datetime import date
from django.db import models
from users.models import Persona
from django.conf import settings
from colegios.models import Colegio
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import UniqueConstraint

class LapsoChoices(models.TextChoices):
    LAPSO_1 = '1', '1er Lapso (Sep-Dic)'
    LAPSO_2 = '2', '2do Lapso (Ene-Mar)'
    LAPSO_3 = '3', '3er Lapso (Abr-Jul)'

class DescriptoresPrimaria(models.TextChoices):
    INICIADO = 'I', 'Iniciado (I)'
    EN_PROCESO = 'EP', 'En Proceso (EP)'
    CONSOLIDADO = 'C', 'Consolidado (C)'

class Seccion(models.Model):
    # Claves estandarizadas para que coincidan exactamente con tu catálogo de asignaturas
    NIVEL_CHOICES = [
        ('INICIAL', 'Inicial'), 
        ('PRIMARIA', 'Primaria'), 
        ('MEDIA_GENERAL', 'Media General'), 
        ('MEDIA_TECNICA', 'Media Técnica')
    ]
    
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE)
    anio_escolar = models.ForeignKey('AnioEscolar', on_delete=models.PROTECT)
    grado = models.CharField(max_length=35) # Ej: "1ro", "1er Año", "Preescolar" 
    nombre = models.CharField(max_length=3)  # Ej: "A", "B", "C"
    capacidad = models.PositiveIntegerField(default=35)
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    es_cuantitativo = models.BooleanField(default=False)
    
    docente_guia = models.ForeignKey(
        'users.Persona', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        limit_choices_to={'tipo': 'DOCENTE'}, # Unificado con CargaAcademica
        related_name='secciones_guiadas'
    )

    class Meta:
        verbose_name = "Sección"
        verbose_name_plural = "Secciones"
        # Evita tener dos secciones "1er Año A" en el mismo año escolar de un mismo colegio
        constraints = [
            UniqueConstraint(fields=['colegio', 'anio_escolar', 'grado', 'nombre'], name='unique_seccion_por_periodo')
        ]

    def __str__(self):
        return f"{self.grado} - Sección {self.nombre} ({self.nivel})"
    
class CargaAcademica(models.Model):
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE, related_name='cargas_academicas')
    asignatura = models.ForeignKey('Asignatura', on_delete=models.PROTECT, related_name='secciones_asignadas')
    
    # Docente titular de la materia en esta sección
    docente = models.ForeignKey(
        'users.Persona', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        limit_choices_to={'tipo': 'DOCENTE'},
        related_name='carga_docente'
    )
    
    # Auxiliar (Muy común para los proyectos de Educación Inicial en Venezuela)
    docente_auxiliar = models.ForeignKey(
        'users.Persona',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='carga_auxiliar'
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Carga Académica"
        verbose_name_plural = "Cargas Académicas"
        # Django 6.x standard: Evita duplicar la misma materia en la misma sección
        constraints = [
            UniqueConstraint(fields=['seccion', 'asignatura'], name='unique_materia_por_seccion')
        ]

    def __str__(self):
        docente_nombre = f" - Prof: {self.docente.apellido}" if self.docente else " - (Sin Profesor)"
        return f"{self.seccion.grado} '{self.seccion.nombre}' -> {self.asignatura.nombre}{docente_nombre}"
    
class Asignatura(models.Model):
    # La asignatura pertenece al colegio y a su catálogo general de materias
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='catalogo_asignaturas')
    
    # Código oficial (Clave para formatos de Zona Educativa / Formato Z)
    codigo = models.CharField(max_length=20, blank=True, null=True, help_text="Ej: MAT-1G, CAS-3G")
    nombre = models.CharField(max_length=120) # Ej: Castellano, Matemática
    descripcion = models.TextField(blank=True, null=True)
    
    # Clasificación pedagógica
    nivel = models.CharField(max_length=20, choices=Seccion.NIVEL_CHOICES) # INICIAL, PRIMARIA, MEDIA_GENERAL, MEDIA_TECNICA
    grado = models.CharField(max_length=35) # Ej: "1ro", "1er Año", "Sala de 5"
    
    # Horas académicas según el plan de estudio del MPPE
    horas_semanales = models.PositiveIntegerField(default=2, help_text="Carga horaria de la materia")
    
    # Banderas para clasificar la materia según su función pedagógica
    es_area_desarrollo = models.BooleanField(default=False, verbose_name="Es Área de Desarrollo (Inicial)")
    es_especialidad = models.BooleanField(default=False, verbose_name="Es Especialidad (Inglés/Música/Deporte)")
    es_tecnica = models.BooleanField(default=False, verbose_name="Es Materia Técnica/Especializada")
    mencion = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Informática, Comercio (Solo para Media Técnica)")

    # Auditoría
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='asignaturas_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True) # Para cuando cambie el currículo nacional, simplemente se desactiva

    def __str__(self):
        mencion_str = f" [{self.mencion}]" if self.mencion else ""
        return f"{self.nombre} - {self.grado} ({self.nivel}){mencion_str}"

# =====================================================================
# 1. EVALUACIÓN CUANTITATIVA (Media General y Media Técnica)
# =====================================================================
class PlanEvaluacion(models.Model):
    """
    Permite al docente dividir el lapso en las 4 a 6 actividades exigidas.
    Ej: "Exposición de Bolívar" - Lapso 1 - 20%
    """
    carga_academica = models.ForeignKey(CargaAcademica, on_delete=models.CASCADE, related_name='planes_evaluacion')
    lapso = models.CharField(max_length=2, choices=LapsoChoices.choices)
    descripcion = models.CharField(max_length=100, help_text="Ej: Taller, Examen, Trabajo Práctico")
    ponderacion = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Porcentaje de la nota total del lapso (1-100)"
    )
    fecha_aplicacion = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.descripcion} ({self.ponderacion}%) - Lapso {self.lapso}"

class NotaCuantitativa(models.Model):
    """
    Almacena las notas del 1 al 20 para Secundaria por cada actividad del plan.
    """
    estudiante = models.ForeignKey(
        'users.Persona', 
        on_delete=models.CASCADE, 
        limit_choices_to={'es_estudiante': True},
        related_name='notas_cuantitativas'
    )
    plan_evaluacion = models.ForeignKey(PlanEvaluacion, on_delete=models.CASCADE, related_name='notas_estudiantes')
    nota = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    observacion = models.CharField(max_length=255, blank=True, null=True)
    
    fecha_registro = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota Cuantitativa"
        verbose_name_plural = "Notas Cuantitativas"
        constraints = [
            # Evita que un estudiante tenga dos notas para la misma actividad del plan
            UniqueConstraint(fields=['estudiante', 'plan_evaluacion'], name='unique_nota_por_actividad')
        ]

    def __str__(self):
        return f"{self.estudiante.apellido} -> {self.plan_evaluacion.descripcion}: {self.nota} pts"

# =====================================================================
# 2. EVALUACIÓN CUALITATIVA (Educación Inicial y Primaria)
# =====================================================================
class InformeCualitativo(models.Model):
    """
    Almacena los boletines informativos descriptivos y los indicadores de logro.
    """
    estudiante = models.ForeignKey(
        'users.Persona', 
        on_delete=models.CASCADE, 
        limit_choices_to={'es_estudiante': True},
        related_name='informes_cualitativos'
    )
    carga_academica = models.ForeignKey(CargaAcademica, on_delete=models.CASCADE, related_name='informes_cualitativos')
    lapso = models.CharField(max_length=2, choices=LapsoChoices.choices)
    
    # Para Primaria: Apreciación global del indicador (I, EP, C)
    descriptor = models.CharField(max_length=3, choices=DescriptoresPrimaria.choices, blank=True, null=True)
    
    # Para Inicial y Primaria: El texto descriptivo del avance pedagógico continuo
    informe_descriptivo = models.TextField(
        blank=True, 
        null=True, 
        help_text="Descripción pedagógica del rendimiento, avances o rasgos de personalidad"
    )
    
    observaciones_recomendaciones = models.TextField(blank=True, null=True, help_text="Sugerencias para el representante")
    fecha_registro = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Informe Cualitativo"
        verbose_name_plural = "Informes Cualitativos"
        constraints = [
            # Un único informe descriptivo por estudiante, materia y lapso
            UniqueConstraint(fields=['estudiante', 'carga_academica', 'lapso'], name='unique_informe_por_lapso')
        ]

    def __str__(self):
        return f"Informe Lapso {self.lapso} - {self.estudiante.apellido} ({self.carga_academica.asignatura.nombre})"
    
# =====================================================================
# 2. EVALUACIÓN CUALITATIVA (Educación Inicial y Primaria)
# =====================================================================
class NotaCualitativa(models.Model):
    """
    Almacena los descriptores (I, EP, C) por cada lapso y asignatura 
    para los estudiantes de Inicial y Primaria.
    """
    estudiante = models.ForeignKey(
        'users.Persona', 
        on_delete=models.CASCADE, 
        limit_choices_to={'es_estudiante': True},
        related_name='notas_cualitativas'
    )
    carga_academica = models.ForeignKey(
        CargaAcademica, 
        on_delete=models.CASCADE, 
        related_name='notas_cualitativas'
    )
    lapso = models.CharField(
        max_length=2, 
        choices=LapsoChoices.choices
    )
    calificacion = models.CharField(
        max_length=2, 
        choices=DescriptoresPrimaria.choices,
        help_text="Iniciado (I), En Proceso (EP) o Consolidado (C)"
    )
    observacion = models.TextField(blank=True, null=True, help_text="Apreciación pedagógica del docente")
    fecha_registro = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota Cualitativa"
        verbose_name_plural = "Notas Cualitativas"
        # Impide duplicar la nota de un estudiante en una misma materia durante el mismo lapso
        constraints = [
            models.UniqueConstraint(
                fields=['estudiante', 'carga_academica', 'lapso'], 
                name='unique_nota_cualitativa_por_lapso'
            )
        ]

    def __str__(self):
        return f"{self.estudiante.apellido} -> {self.carga_academica.asignatura.nombre} (Lapso {self.lapso}): {self.get_calificacion_display()}"
    
class AnioEscolar(models.Model):
    """Ej: 2025-2026"""    
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=10, unique=True)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    matricula1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Costo de la matrícula para Inicial
    matricula2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Costo de la matrícula para Primaria
    matricula3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Costo de la matrícula para Secundaria
    mensualidad1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Costo base de la mensualidad para Inicial
    mensualidad2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Costo base de la mensualidad para Primaria
    mensualidad3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Costo base de la mensualidad para Secundaria

    def __str__(self):
        return self.nombre
    
class Pago(models.Model):
    METODOS_PAGO = (
        ('transferencia', 'Transferencia Bancaria'),
        ('pago_movil', 'Pago Móvil'),
        ('efectivo', 'Efectivo en Divisas'),
        ('efectivo_bs', 'Efectivo en Bs'),
        ('zelle', 'Zelle'),
        ('punto', 'Punto de Venta'),
    )

    TIPO_PAGO = (
        ('matricula', 'Matrícula'),
        ('mensualidad', 'Mensualidad'),
        ('extraordinario', 'Pago Extraordinario'),
    )

    BANCOS = (         
        ('venezuela', 'VENEZUELA'),         
        ('provincial', 'PROVINCIAL'),
        ('mercantil', 'MERCANTIL'), 
        ('banesco', 'BANESCO'), 
        ('sofitasa', 'SOFITASA'),
        ('caribe', 'BANCO CARIBE'),
        ('exterior', 'BANCO EXTERIOR'),
        ('tesoro', 'BANCO DEL TESORO'), 
        ('bvc', 'BANCO VENEZOLANO DE CRÉDITO'),
        ('caroni', 'BANCO CARONÍ'),
        ('plaza', 'BANCO PLAZA'),
        ('bangente', 'BANCO BANGENTE'),
        ('bfc', 'BANCO FONDO COMÚN'),
        ('del_sur', 'BANCO DEL SUR'),
        ('100banco', '100% BANCO'),
        ('bancrecer', 'BANCRECER'),
        ('activo', 'BANCO ACTIVO'),
        ('bancamiga', 'BANCAMIGA'),
        ('banplus', 'BANPLUS'),
        ('bfa', 'BCO FUERZA ARMADA NAC BOL'),
        ('bnc', 'BANCO NAC DE CRÉDITO'),
        ('otro', 'OTRO'),
    )

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='pagos') 
    anio_escolar = models.ForeignKey('AnioEscolar', on_delete=models.PROTECT, related_name='pagos')
    representante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pagos_realizados')
    estudiante = models.ForeignKey('users.Persona', on_delete=models.PROTECT, related_name='pagos_recibidos', limit_choices_to={'es_estudiante': True})
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO, default='mensualidad')
    monto = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto de la cuota")
    metodo_pago = models.CharField(max_length=25, choices=METODOS_PAGO, default='transferencia', blank=True, null=True)
    num_referencia = models.CharField(max_length=100, blank=True, null=True, help_text="Número de referencia bancaria o recibo")
    monto_bs = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Monto en Bolívares que deposito el representante")
    banco = models.CharField(max_length=50, choices=BANCOS, blank=True, null=True, help_text="Banco desde el cual se realizó el pago")
    titular_cuenta = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre del titular de la cuenta desde la que se realizó el pago")
    num_cuota = models.CharField(max_length=25, help_text="Ej: 'UNICA' para matrícula/especiales, o del '1' al '12' para mensualidades")
    fecha_vencimiento = models.DateField(blank=True, null=True, help_text="Fecha de vencimiento del pago")
    fecha_pago = models.DateField(blank=True, null=True, help_text="Fecha en la que el representante realizó/se validó el pago")
    detalle = models.TextField(blank=True, null=True, help_text="Concepto. Ej: Mensualidad Octubre")
    pagado = models.BooleanField(default=False, help_text="Indica si el pago ya fue procesado y verificado")
    comprobante = models.ImageField(upload_to='pagos/comprobantes/%Y/%m/', blank=True, null=True, help_text="Captura o foto del comprobante")
    activo = models.BooleanField(default=True, help_text="Falso significa que el pago fue anulado/borrado")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    motivo = models.TextField(blank=True, null=True, help_text="Motivo de anulación o corrección, si aplica")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_modificados', help_text="Usuario que modificó o anuló el pago, si aplica")

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['fecha_vencimiento', 'id'] # Ordenados cronológicamente por vencimiento

    def __str__(self):
        return f"{self.get_tipo_pago_display()} - Cuota {self.num_cuota} | {self.estudiante} ({'PAGADO' if self.pagado else 'PENDIENTE'})"

    def anular(self, usuario, motivo):
        self.activo = False
        self.usuario = usuario
        self.motivo = motivo
        self.save()

class TasaCambio(models.Model):
    moneda = models.CharField(max_length=3, default="USD")
    fecha = models.DateField(unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=4)
    es_manual = models.BooleanField(default=False) # Para el color naranja
    es_estimado = models.BooleanField(default=False) # Para el color rojo
    fecha_actualizacion = models.DateTimeField(auto_now=True) # Se actualiza solo al guardar
    
    usuario_edicion = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name="tasas_editadas"
    )

    class Meta:
        ordering = ['-fecha', '-fecha_actualizacion']
        # Evita que se duplique la moneda el mismo día si corres scripts manuales
        unique_together = ('moneda', 'fecha') 

    def __str__(self):
        return f"{self.moneda}: {self.precio} ({self.fecha})"

class Inscripcion(models.Model):
    ESTADOS = [
        ('ACTIVO', 'Activo'),
        ('RETIRADO', 'Retirado'),
        ('GRADUADO', 'Graduado'),
    ]

    estudiante = models.ForeignKey(
        'users.Persona', 
        on_delete=models.CASCADE, 
        related_name='inscripciones',
        limit_choices_to={'es_estudiante': True}
    )
    seccion = models.ForeignKey(Seccion, on_delete=models.PROTECT)
    anio_escolar = models.ForeignKey(AnioEscolar, on_delete=models.PROTECT)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    
    # IMPORTANTE: El costo se guarda aquí por si el estudiante tiene 
    # una beca o descuento especial ese año.
    costo_mensualidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_matricula = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='ACTIVO')

    class Meta:
        # Evita que un estudiante se inscriba dos veces en el mismo año
        unique_together = ('estudiante', 'anio_escolar')

    def __str__(self):
        return f"{self.estudiante} - {self.seccion} ({self.anio_escolar})"
    
class EstudianteDetalle(models.Model):
    # Extendemos la Persona de tipo 'ESTUDIANTE'
    estudiante = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name='detalle_academico')
    seccion = models.ForeignKey('Seccion', on_delete=models.SET_NULL, null=True) 
    becado = models.BooleanField(default=False)
    porcentaje_beca = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.estudiante} en {self.seccion}"

class RepresentanteDetalle(models.Model):
    # Extendemos la Persona de tipo 'REPRESENTANTE'
    representante = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name='detalle_representante') 
    
    def __str__(self):
        return f"Detalle de {self.representante.nombre}"

class AdministrativoDetalle(models.Model):
    # Vinculamos a la Persona (que debe ser de tipo es_admin=True)
    administrativo = models.OneToOneField(
        'users.Persona', 
        on_delete=models.CASCADE, 
        related_name='detalle_laboral'
    )
    cargo = models.CharField(max_length=100)
    fecha_inicio = models.DateField()

    def __str__(self):
        return f"{self.administrativo.nombre} - {self.cargo}"

class DocenteDetalle(models.Model):
    # Vinculamos 1 a 1 con la Persona de tipo 'DOCENTE'
    docente = models.OneToOneField(
        'users.Persona', 
        on_delete=models.CASCADE, 
        related_name='detalle_docente'
    )
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Detalle de {self.docente.nombre}"
