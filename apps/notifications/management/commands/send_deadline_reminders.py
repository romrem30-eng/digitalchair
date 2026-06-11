from django.core.management.base import BaseCommand

from apps.notifications.telegram import create_deadline_reminders


class Command(BaseCommand):

    help = 'Создает напоминания о приближении дедлайнов и отправляет их в Telegram при наличии привязки.'

    def add_arguments(self, parser):

        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='За сколько дней до срока создавать напоминание.'
        )

    def handle(self, *args, **options):

        created_count = create_deadline_reminders(
            days=options['days']
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Создано напоминаний: {created_count}.'
            )
        )
