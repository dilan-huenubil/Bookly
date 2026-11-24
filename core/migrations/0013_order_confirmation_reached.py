from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0012_profile_role_book_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='confirmation_reached',
            field=models.BooleanField(default=False, verbose_name='Llegó a confirmación'),
        ),
    ]
