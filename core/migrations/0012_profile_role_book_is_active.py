from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_order_estimated_delivery_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Activo en catálogo'),
        ),
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(
                choices=[('user', 'Usuario'), ('admin', 'Administrador')],
                default='user',
                max_length=16,
                verbose_name='Rol',
            ),
        ),
    ]