from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fundacion_app', '0006_migrate_gastos_to_movimientos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimientocaja',
            name='hogar',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='movimientos',
                to='fundacion_app.hogares',
            ),
        ),
    ]
