from django.db import migrations


def migrate_gastos_to_movimientos(apps, schema_editor):
    Hogares = apps.get_model('fundacion_app', 'Hogares')
    Gasto = apps.get_model('fundacion_app', 'Gasto')
    MovimientoCaja = apps.get_model('fundacion_app', 'MovimientoCaja')

    default_hogar, _ = Hogares.objects.get_or_create(
        nombre='Sin Asignar',
        defaults={
            'direccion': 'Pendiente',
            'telefono': 'Pendiente',
            'email': 'pendiente@fundacion.org',
            'contacto': 'Pendiente',
        }
    )

    for gasto in Gasto.objects.all():
        MovimientoCaja.objects.create(
            hogar=default_hogar,
            tipo='egreso',
            fecha=gasto.fecha,
            descripcion=gasto.descripcion,
            categoria=gasto.categoria,
            monto=gasto.monto,
            pagado=gasto.pagado,
            gasto_origen_id=gasto.pk,
        )


def reverse_migration(apps, schema_editor):
    MovimientoCaja = apps.get_model('fundacion_app', 'MovimientoCaja')
    MovimientoCaja.objects.filter(tipo='egreso', gasto_origen_id__isnull=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('fundacion_app', '0005_hogares_and_movimientocaja'),
    ]

    operations = [
        migrations.RunPython(migrate_gastos_to_movimientos, reverse_migration),
    ]
