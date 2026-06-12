#users/models.py
from datetime import date
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

class UsuarioManager(BaseUserManager): # Manager personalizado para el modelo Usuario
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El Email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractUser):    # Modelo personalizado de Usuario
    username = None # Eliminamos el username
    email = models.EmailField('Correo Electrónico', unique=True)
    
    # Vinculamos al usuario con un colegio (puede ser null para el SuperUser)
    colegio = models.ForeignKey('colegios.Colegio', on_delete=models.CASCADE, null=True, blank=True)
    
    # Campo para asignar el Rol (lo crearemos a continuación)
    rol = models.ForeignKey('Rol', on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    def __str__(self):
        return self.email

class Rol(models.Model): # Modelo para definir los roles y sus permisos
    nombre = models.CharField(max_length=50)
    colegio = models.ForeignKey('colegios.Colegio', on_delete=models.CASCADE)
    
    # Permisos como booleanos (los "checks")
    # Módulo Contenido
    can_manage_news = models.BooleanField('Gestionar Noticias', default=False)
    can_manage_gallery = models.BooleanField('Gestionar Galería', default=False)
    
    # Módulo Personas
    can_manage_staff = models.BooleanField('Gestionar Personal', default=False)
    can_manage_students = models.BooleanField('Gestionar Alumnos/Reps', default=False)
    
    # Módulo Académico
    can_manage_grades = models.BooleanField('Gestionar Calificaciones', default=False)
    
    # Módulo Finanzas
    can_manage_finances = models.BooleanField('Gestionar Cobros/Pagos', default=False)
    
    # Módulo Cantina
    can_manage_canteen = models.BooleanField('Gestionar Cantina', default=False)

    def __str__(self):
        return f"{self.nombre} ({self.colegio.nombre})"
    
class Persona(models.Model):
    TIPOS = [
        ('DOCENTE', 'Docente'),
        ('ADMIN', 'Administrativo'),
        ('REPRESENTANTE', 'Representante'),
        ('ESTUDIANTE', 'Estudiante'),
        ('CANTINA', 'Personal de Cantina'),
    ]

    # Relación con el sistema de autenticación
    # null=True porque un Estudiante pequeño quizás no tenga usuario aún
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, null=True, blank=True, related_name='perfil')
    colegio = models.ForeignKey('colegios.Colegio', on_delete=models.CASCADE)
    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)   
    direccion = models.TextField(blank=True, null=True)  
    fecha_nacimiento = models.DateField(null=True, blank=True)
    profesion = models.CharField(max_length=100, blank=True, null=True)   
    es_docente = models.BooleanField(default=False)
    es_admin = models.BooleanField(default=False)
    es_representante = models.BooleanField(default=False)
    es_estudiante = models.BooleanField(default=False)
    es_cantina = models.BooleanField(default=False)
    tipo = models.CharField(max_length=20, choices=TIPOS, blank=True, null=True) 
    activo = models.BooleanField(default=True)
    foto = models.ImageField(upload_to='estudiantes/fotos/', null=True, blank=True)

    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = date.today() 
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return "N/A"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.tipo})"

class RelacionFamiliar(models.Model):
    representante = models.ForeignKey(
        Persona, 
        on_delete=models.CASCADE, 
        related_name='representados', 
        limit_choices_to={'tipo': 'REPRESENTANTE'}
    )
    estudiante = models.ForeignKey(
        Persona, 
        on_delete=models.CASCADE, 
        related_name='tutores', 
        limit_choices_to={'tipo': 'ESTUDIANTE'}
    )
    parentesco = models.CharField(max_length=50)

    # =====================================================================
# 1. CONTROL DE SALDOS (PREPAGO)
# =====================================================================

class BilleteraCantina(models.Model):
    """
    Cuenta prepago individual por alumno. 
    Se crea automáticamente al inscribirse el estudiante.
    """
    estudiante = models.OneToOneField(
        'users.Persona', 
        on_delete=models.CASCADE, 
        limit_choices_to={'es_estudiante': True},
        related_name='billetera_cantina'
    )
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Billetera Cantina"
        verbose_name_plural = "Billeteras Cantina"

    def __str__(self):
        return f"Billetera: {self.estudiante.apellido}, {self.estudiante.nombre} | Saldo: {self.saldo} BS"


# =====================================================================
# 2. CATÁLOGO DE RUBROS (PRECIOS DINÁMICOS)
# =====================================================================

class RubroCantina(models.Model):
    """
    Segmentos de productos vendidos en la cantina.
    Aislados por colegio para que cada cantina arrendada maneje su catálogo.
    """
    colegio = models.ForeignKey('colegios.Colegio', on_delete=models.CASCADE, related_name='rubros_cantina')
    nombre = models.CharField(max_length=100, help_text="Ej: PASTELES, REFRESCOS, CHUCHERIAS")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Rubro de Cantina"
        verbose_name_plural = "Rubros de Cantina"
        constraints = [
            models.UniqueConstraint(fields=['colegio', 'nombre'], name='unique_rubro_por_colegio')
        ]

    def __str__(self):
        return f"{self.nombre} ({self.colegio.slug})"


# =====================================================================
# 3. TRANSACCIONES: RECARGAS Y CONSUMOS
# =====================================================================

class RecargaBilletera(models.Model):
    """
    Historial de dinero inyectado por el representante a la billetera del alumno.
    """
    METODOS_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('PAGO_MOVIL', 'Pago Móvil'),
        ('TRANSFERENCIA', 'Transferencia'),
    ]

    billetera = models.ForeignKey(BilleteraCantina, on_delete=models.CASCADE, related_name='recargas')
    representante = models.ForeignKey(
        'users.Persona', 
        on_delete=models.PROTECT, 
        limit_choices_to={'es_representante': True},
        help_text="Quién realiza el aporte"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text="Número de Tx o captura")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        'users.Persona', 
        on_delete=models.PROTECT, 
        limit_choices_to={'es_cantina': True},
        related_name='recargas_procesadas',
        help_text="Cantinero que recibió el dinero"
    )

    class Meta:
        verbose_name = "Recarga de Billetera"
        verbose_name_plural = "Recargas de Billeteras"

    def __str__(self):
        return f"Recarga {self.id} -> +{self.monto} BS a {self.billetera.estudiante.apellido}"

class VentaCantina(models.Model):
    """
    Encabezado del ticket de consumo del estudiante en la cantina.
    """
    billetera = models.ForeignKey(BilleteraCantina, on_delete=models.CASCADE, related_name='consumos')
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        'users.Persona', 
        on_delete=models.PROTECT, 
        limit_choices_to={'es_cantina': True},
        related_name='ventas_procesadas'
    )

    class Meta:
        verbose_name = "Consumo en Cantina"
        verbose_name_plural = "Consumos en Cantina"

    def __str__(self):
        return f"Ticket Venta #{self.id} - Alumno: {self.billetera.estudiante.apellido} - Total: {self.monto_total} BS"


class DetalleVentaCantina(models.Model):
    """
    Líneas de renglones comprados en una venta específica.
    Permite almacenar el precio manual/dinámico que asignó el cantinero en ese instante.
    """
    venta = models.ForeignKey(VentaCantina, on_delete=models.CASCADE, related_name='detalles')
    rubro = models.ForeignKey(RubroCantina, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, help_text="Precio fijado en el momento")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # El subtotal se autocalcula siempre para evitar discrepancias aritméticas
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.rubro.nombre} (Venta #{self.venta.id})"


