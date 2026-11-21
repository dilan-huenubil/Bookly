from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0017_bookrecommendation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tracking_status',
            field=models.CharField(
                choices=[
                    ('solicitud_compra', 'Solicitud de compra'),
                    ('confirmacion_productos', 'Confirmación de productos'),
                    ('preparando', 'Preparando Pedido'),
                    ('en_camino', 'En Camino'),
                    ('entregado', 'Entregado'),
                ],
                default='solicitud_compra',
                max_length=30,
                verbose_name='Estado de seguimiento',
            ),
        ),
    ]
