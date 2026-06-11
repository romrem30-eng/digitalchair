from django.conf import settings
from django.db import migrations
from django.db import models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_workloadplan_approved_at'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('import_type', models.CharField(choices=[('teachers', 'Преподаватели'), ('subjects', 'Дисциплины'), ('groups', 'Учебные группы'), ('workload', 'Учебный план нагрузки')], max_length=30)),
                ('records_count', models.PositiveIntegerField(default=0)),
                ('result', models.CharField(choices=[('SUCCESS', 'Успешно'), ('FAILED', 'С ошибками')], max_length=20)),
                ('details', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_logs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
