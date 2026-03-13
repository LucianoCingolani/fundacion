from django.db import models

class Donante(models.Model):
    TRATO_CHOICES = [('Sr', 'Sr.'), ('Sra', 'Sra.'), ('Sres', 'Sres.')]
    GENERO_CHOICES = [('H', 'Hombre'), ('M', 'Mujer'), ('O', 'Otro')]
    ORIGEN_CHOICES = [
        ('Redes', 'Redes Sociales'),
        ('Evento', 'Evento'),
        ('Referido', 'Referido'),
        ('Difusion', 'Acción de Difusión'),
    ]
    TIPO_CHOICES = [('Recurrente', 'Recurrente'), ('Eventual', 'Eventual'), ('UnicaVez', 'Única Vez')]

    # Campos de Gestión
    seguido_por = models.CharField(max_length=100, verbose_name="Quien lo sigue/llamador")
    origen = models.CharField(max_length=50, choices=ORIGEN_CHOICES)
    referente = models.CharField(max_length=100, blank=True, null=True)
    segmentacion = models.CharField(max_length=100, blank=True)

    # Datos Personales
    trato = models.CharField(max_length=10, choices=TRATO_CHOICES)
    genero = models.CharField(max_length=10, choices=GENERO_CHOICES)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    
    # Datos Profesionales
    empresa = models.CharField(max_length=150, blank=True)
    cargo = models.CharField(max_length=150, blank=True)
    
    # Contacto
    celular = models.CharField(max_length=50)
    mail = models.EmailField()

    # Datos de Donación
    tipo_donante = models.CharField(max_length=20, choices=TIPO_CHOICES)
    monto_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_alta = models.DateField()
    fecha_baja = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    

class Donacion(models.Model):
    METODO_CHOICES = [
        ('Transferencia', 'Transferencia'),
        ('Efectivo', 'Efectivo'),
        ('Tarjeta', 'Tarjeta'),
        ('Otro', 'Otro'),
    ]

    donante = models.ForeignKey(Donante, on_delete=models.CASCADE, related_name='donaciones')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateField()
    metodo = models.CharField(max_length=50, choices=METODO_CHOICES)
    comprobante = models.CharField(max_length=100, blank=True, help_text="Nro de operación o referencia")
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.donante} - ${self.monto} ({self.fecha_pago})"