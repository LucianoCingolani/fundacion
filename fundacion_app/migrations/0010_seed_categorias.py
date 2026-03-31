from django.db import migrations

CATEGORIAS_INGRESO = [
    'Eventos (campañas)',
    'Donantes anónimos',
    'Becas provincia',
    'Donar online',
    'Feria americana',
    'AUH',
]

CATEGORIAS_EGRESO = [
    'Gastos generales',
    'Servicios',
    'Alquiler',
    'Materiales',
    'Personal',
]


def seed_categorias(apps, schema_editor):
    CategoriaGasto = apps.get_model('fundacion_app', 'CategoriaGasto')

    for nombre in CATEGORIAS_INGRESO:
        CategoriaGasto.objects.get_or_create(
            nombre=nombre,
            tipo_movimiento='ingreso',
            defaults={'tipo': ''},
        )

    for nombre in CATEGORIAS_EGRESO:
        CategoriaGasto.objects.get_or_create(
            nombre=nombre,
            tipo_movimiento='egreso',
            defaults={'tipo': ''},
        )


def reverse_seed(apps, schema_editor):
    CategoriaGasto = apps.get_model('fundacion_app', 'CategoriaGasto')
    todos = CATEGORIAS_INGRESO + CATEGORIAS_EGRESO
    CategoriaGasto.objects.filter(nombre__in=todos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('fundacion_app', '0009_categoria_tipo_movimiento'),
    ]

    operations = [
        migrations.RunPython(seed_categorias, reverse_seed),
    ]
