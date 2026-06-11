from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from apps.core.models import Teacher


def validate_attachment_size(file):

    max_size = 5 * 1024 * 1024

    if file.size > max_size:

        raise ValidationError(
            'Размер файла не должен превышать 5 МБ.'
        )


class Task(models.Model):

    class Statuses(models.TextChoices):

        NEW = 'NEW', 'Новая'
        IN_PROGRESS = 'IN_PROGRESS', 'В работе'
        COMPLETED = 'COMPLETED', 'Выполнена'
        CANCELLED = 'CANCELLED', 'Отменена'

    class Priorities(models.TextChoices):

        LOW = 'LOW', 'Низкий'
        MEDIUM = 'MEDIUM', 'Средний'
        HIGH = 'HIGH', 'Высокий'

    title = models.CharField(
        max_length=255
    )

    description = models.TextField()

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )

    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Statuses.choices,
        default=Statuses.NEW
    )

    priority = models.CharField(
        max_length=20,
        choices=Priorities.choices,
        default=Priorities.MEDIUM
    )

    attachment = models.FileField(
        upload_to='assignments/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf',
                    'docx',
                    'xlsx',
                    'png',
                    'jpg',
                    'jpeg',
                ]
            ),
            validate_attachment_size
        ]
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):

        if self.status == self.Statuses.COMPLETED and self.completed_at is None:

            self.completed_at = timezone.now()

        elif self.status != self.Statuses.COMPLETED:

            self.completed_at = None

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):

        return (
            self.due_date < timezone.localdate()
            and self.status != self.Statuses.COMPLETED
        )

    def __str__(self):

        return self.title
