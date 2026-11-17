from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0013_order_confirmation_reached'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='stock_updated',
            field=models.BooleanField(default=False, verbose_name='Stock actualizado'),
        ),
    ]