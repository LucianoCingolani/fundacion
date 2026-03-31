from django.db import models

class Hogares(models.Model):
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    contacto = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nombre

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
    
class CategoriaGasto(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [('ingreso', 'Ingreso'), ('egreso', 'Egreso')]

    nombre = models.CharField(max_length=100)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES, default='egreso')
    tipo = models.CharField(max_length=50, choices=[('F', 'Fijo'), ('V', 'Variable')], blank=True)

    def __str__(self):
        return self.nombre

class Gasto(models.Model):
    fecha = models.DateField()
    descripcion = models.CharField(max_length=255)
    categoria = models.ForeignKey(CategoriaGasto, on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    # Útil para el contador: ¿Se pagó o está pendiente?
    pagado = models.BooleanField(default=True)
    comprobante = models.FileField(upload_to='gastos/comprobantes/', null=True, blank=True)

    def __str__(self):
        return f"{self.fecha} - {self.descripcion} - ${self.monto}"


class MovimientoCaja(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]
    METODO_CHOICES = [
        ('Transferencia', 'Transferencia'),
        ('Efectivo', 'Efectivo'),
        ('Tarjeta', 'Tarjeta'),
        ('Otro', 'Otro'),
    ]

    hogar = models.ForeignKey(Hogares, on_delete=models.PROTECT, related_name='movimientos', null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha = models.DateField()
    descripcion = models.CharField(max_length=255)
    categoria = models.ForeignKey(CategoriaGasto, on_delete=models.PROTECT, null=True, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=50, choices=METODO_CHOICES, default='Transferencia')
    pagado = models.BooleanField(default=True)
    comprobante = models.FileField(upload_to='cashflow/comprobantes/', null=True, blank=True)
    notas = models.TextField(blank=True)
    gasto_origen_id = models.IntegerField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} | {self.hogar} | ${self.monto} ({self.fecha})"