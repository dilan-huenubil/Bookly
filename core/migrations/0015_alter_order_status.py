from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0014_order_stock_updated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('created', 'Creada'),
                    ('paid', 'Pagada'),
                    ('canceled', 'Cancelado'),
                    ('error', 'Error'),
                ],
                default='created',
                max_length=16,
                verbose_name='Estado',
            ),
        ),
    ]
