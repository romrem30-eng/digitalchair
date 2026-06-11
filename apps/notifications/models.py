from django.conf import settings
from django.db import models


class Notification(models.Model):

    class Types(models.TextChoices):

        NEW_TASK = 'NEW_TASK', 'Новое поручение'
        STATUS_CHANGED = 'STATUS_CHANGED', 'Изменение статуса'
        TASK_COMPLETED = 'TASK_COMPLETED', 'Завершение поручения'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    task = models.ForeignKey(
        'assignments.Task',
        on_delete=models.CASCADE,
        related_name='notifications',
        blank=True,
        null=True
    )

    notification_type = models.CharField(
        max_length=30,
        choices=Types.choices
    )

    title = models.CharField(
        max_length=255
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.title


def create_task_notification(
    recipient,
    task,
    notification_type
):

    if notification_type == Notification.Types.NEW_TASK:

        title = 'Новое поручение'
        message = f'Вам назначено новое поручение: {task.title}.'

    elif notification_type == Notification.Types.TASK_COMPLETED:

        title = 'Поручение выполнено'
        message = f'Поручение "{task.title}" отмечено как выполненное.'

    else:

        title = 'Статус поручения изменен'
        message = (
            f'Статус поручения "{task.title}" изменен на '
            f'"{task.get_status_display()}".'
        )

    return Notification.objects.create(
        recipient=recipient,
        task=task,
        notification_type=notification_type,
        title=title,
        message=message
    )
