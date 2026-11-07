from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0015_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='deletion_requested_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Eliminación solicitada el',
            ),
        ),
    ]
