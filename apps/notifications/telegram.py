import os
import secrets
from datetime import timedelta

from asgiref.sync import async_to_sync
from django.utils import timezone

from apps.assignments.models import Task
from apps.notifications.models import Notification


TELEGRAM_BIND_CODE_TTL_MINUTES = 15


def get_telegram_bot_token():

    return os.getenv(
        'TELEGRAM_BOT_TOKEN',
        ''
    ).strip()


def telegram_bot_is_configured():

    return bool(get_telegram_bot_token())


def get_telegram_bot():

    token = get_telegram_bot_token()

    if not token:

        return None

    try:

        from telegram import Bot

    except ImportError:

        return None

    return Bot(token=token)


def send_telegram_text(telegram_id, text):

    bot = get_telegram_bot()

    if bot is None or not telegram_id:

        return False

    try:

        async_to_sync(bot.send_message)(
            chat_id=telegram_id,
            text=text
        )

    except Exception:

        return False

    return True


def format_notification_message(notification):

    return (
        f'{notification.title}\n\n'
        f'{notification.message}'
    )


def send_notification_to_telegram(notification):

    recipient = notification.recipient

    if not getattr(recipient, 'telegram_id', None):

        return False

    return send_telegram_text(
        recipient.telegram_id,
        format_notification_message(notification)
    )


def generate_telegram_bind_code(user):

    while True:

        code = ''.join(
            secrets.choice('0123456789')
            for _ in range(6)
        )

        if not user.__class__.objects.filter(
            telegram_bind_code=code
        ).exclude(
            pk=user.pk
        ).exists():

            break

    user.telegram_bind_code = code
    user.telegram_bind_code_created_at = timezone.now()
    user.save(
        update_fields=[
            'telegram_bind_code',
            'telegram_bind_code_created_at',
        ]
    )

    return code


def clear_telegram_bind_code(user):

    user.telegram_bind_code = None
    user.telegram_bind_code_created_at = None
    user.save(
        update_fields=[
            'telegram_bind_code',
            'telegram_bind_code_created_at',
        ]
    )


def unbind_telegram_account(user):

    user.telegram_id = None
    user.telegram_bind_code = None
    user.telegram_bind_code_created_at = None
    user.save(
        update_fields=[
            'telegram_id',
            'telegram_bind_code',
            'telegram_bind_code_created_at',
        ]
    )


def is_bind_code_valid(user, code):

    if (
        not code
        or user.telegram_bind_code != code
        or user.telegram_bind_code_created_at is None
    ):

        return False

    expires_at = user.telegram_bind_code_created_at + timedelta(
        minutes=TELEGRAM_BIND_CODE_TTL_MINUTES
    )

    return timezone.now() <= expires_at


def bind_user_to_telegram(code, telegram_id):

    normalized_code = str(code).strip()

    if not normalized_code:

        return None, 'Код привязки не указан.'

    user_model = Task._meta.get_field('created_by').remote_field.model

    user = user_model.objects.filter(
        telegram_bind_code=normalized_code
    ).first()

    if user is None:

        return None, 'Код привязки не найден или уже недействителен.'

    if not is_bind_code_valid(user, normalized_code):

        clear_telegram_bind_code(user)

        return None, 'Срок действия кода истек. Сгенерируйте новый код в веб-интерфейсе.'

    existing_owner = user_model.objects.filter(
        telegram_id=str(telegram_id)
    ).exclude(
        pk=user.pk
    ).first()

    if existing_owner is not None:

        return None, 'Этот Telegram-аккаунт уже привязан к другому пользователю.'

    user.telegram_id = str(telegram_id)
    user.telegram_bind_code = None
    user.telegram_bind_code_created_at = None
    user.save(
        update_fields=[
            'telegram_id',
            'telegram_bind_code',
            'telegram_bind_code_created_at',
        ]
    )

    return user, 'Аккаунт успешно привязан к Telegram.'


def get_active_tasks_for_user(user):

    teacher = getattr(
        user,
        'teacher_profile',
        None
    )

    if teacher is None:

        return Task.objects.none()

    return Task.objects.filter(
        teacher=teacher
    ).exclude(
        status__in=(
            Task.Statuses.COMPLETED,
            Task.Statuses.CANCELLED,
        )
    ).order_by(
        'due_date',
        'id'
    )


def build_start_message():

    return (
        'Добро пожаловать в DigitalChair Bot.\n\n'
        'Доступные команды:\n'
        '/start - приветствие и инструкция\n'
        '/help - список команд\n'
        '/bind <код> - привязать аккаунт\n'
        '/tasks - показать активные поручения\n'
        '/task <id> done - отметить поручение выполненным'
    )


def build_help_message():

    return (
        'Команды бота:\n'
        '/start\n'
        '/help\n'
        '/bind <код>\n'
        '/tasks\n'
        '/task <id> done'
    )


def build_tasks_message(user):

    tasks = list(
        get_active_tasks_for_user(user)
    )

    if not tasks:

        return 'Активных поручений нет.'

    lines = ['Активные поручения:']

    for task in tasks:

        lines.append(
            (
                f'#{task.id} | {task.title} | '
                f'срок: {task.due_date:%d.%m.%Y} | '
                f'статус: {task.get_status_display()}'
            )
        )

    return '\n'.join(lines)


def complete_task_via_telegram(user, task_id):

    teacher = getattr(
        user,
        'teacher_profile',
        None
    )

    if teacher is None:

        return False, 'Профиль преподавателя не найден.'

    task = Task.objects.filter(
        teacher=teacher,
        pk=task_id
    ).select_related(
        'created_by'
    ).first()

    if task is None:

        return False, 'Поручение не найдено.'

    if task.status == Task.Statuses.CANCELLED:

        return False, 'Отмененное поручение нельзя завершить.'

    if task.status == Task.Statuses.COMPLETED:

        return False, 'Поручение уже отмечено как выполненное.'

    task.status = Task.Statuses.COMPLETED
    task.save()

    from apps.notifications.models import create_task_notification

    create_task_notification(
        task.created_by,
        task,
        Notification.Types.TASK_COMPLETED
    )

    return True, f'Поручение #{task.id} отмечено как выполненное.'


def create_deadline_reminders(days=1):

    today = timezone.localdate()
    target_date = today + timedelta(days=days)
    created_count = 0

    tasks = Task.objects.select_related(
        'teacher',
        'teacher__user'
    ).filter(
        due_date=target_date
    ).exclude(
        status__in=(
            Task.Statuses.COMPLETED,
            Task.Statuses.CANCELLED,
        )
    )

    from apps.notifications.models import create_notification

    for task in tasks:

        recipient = task.teacher.user
        title = 'Приближается срок поручения'
        message = (
            f'Поручение "{task.title}" нужно выполнить до '
            f'{task.due_date:%d.%m.%Y}.'
        )

        already_exists = Notification.objects.filter(
            recipient=recipient,
            task=task,
            title=title,
            created_at__date=today
        ).exists()

        if already_exists:

            continue

        create_notification(
            recipient=recipient,
            task=task,
            notification_type=Notification.Types.STATUS_CHANGED,
            title=title,
            message=message
        )

        created_count += 1

    return created_count


def notify_workload_approved(plan):

    department = getattr(
        plan,
        'кафедра',
        str(plan)
    )

    from apps.notifications.models import create_notification

    seen_recipient_ids = set()

    for assignment in plan.assignments.select_related(
        'teacher',
        'teacher__user'
    ):

        recipient = assignment.teacher.user

        if recipient.id in seen_recipient_ids:

            continue

        seen_recipient_ids.add(recipient.id)

        create_notification(
            recipient=recipient,
            task=None,
            notification_type=Notification.Types.STATUS_CHANGED,
            title='Учебная нагрузка утверждена',
            message=(
                f'План нагрузки кафедры "{department}" '
                f'за {plan.academic_year} утвержден.'
            )
        )
