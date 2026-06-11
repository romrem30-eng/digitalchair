from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_2fa_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='telegram_bind_code',
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='telegram_bind_code_created_at',
            field=models.DateTimeField(
                blank=True,
                null=True
            ),
        ),
    ]
