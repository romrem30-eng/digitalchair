from django.core.management.base import BaseCommand

from apps.notifications.telegram import bind_user_to_telegram
from apps.notifications.telegram import build_help_message
from apps.notifications.telegram import build_start_message
from apps.notifications.telegram import build_tasks_message
from apps.notifications.telegram import complete_task_via_telegram
from apps.notifications.telegram import get_telegram_bot_token


class Command(BaseCommand):

    help = 'Запускает Telegram-бота DigitalChair.'

    def handle(self, *args, **options):

        token = get_telegram_bot_token()

        if not token:

            self.stdout.write(
                self.style.WARNING(
                    'TELEGRAM_BOT_TOKEN не задан. Бот не запущен.'
                )
            )

            return

        try:

            from telegram import Update
            from telegram.ext import ApplicationBuilder
            from telegram.ext import CommandHandler
            from telegram.ext import ContextTypes

        except ImportError as exc:

            raise RuntimeError(
                'Для Telegram-бота требуется библиотека python-telegram-bot.'
            ) from exc

        async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

            await update.message.reply_text(
                build_start_message()
            )

        async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

            await update.message.reply_text(
                build_help_message()
            )

        async def bind_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

            if not context.args:

                await update.message.reply_text(
                    'Используйте: /bind <код>'
                )

                return

            user, message = bind_user_to_telegram(
                context.args[0],
                update.effective_user.id
            )

            await update.message.reply_text(message)

            if user is not None:

                await update.message.reply_text(
                    'Привязка подтверждена. Теперь вы будете получать уведомления в Telegram.'
                )

        async def tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

            from apps.users.models import User

            user = User.objects.filter(
                telegram_id=str(update.effective_user.id)
            ).first()

            if user is None:

                await update.message.reply_text(
                    'Аккаунт не привязан. Сначала выполните /bind <код>.'
                )

                return

            await update.message.reply_text(
                build_tasks_message(user)
            )

        async def task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

            from apps.users.models import User

            user = User.objects.filter(
                telegram_id=str(update.effective_user.id)
            ).first()

            if user is None:

                await update.message.reply_text(
                    'Аккаунт не привязан. Сначала выполните /bind <код>.'
                )

                return

            if len(context.args) != 2 or context.args[1].lower() != 'done':

                await update.message.reply_text(
                    'Используйте: /task <id> done'
                )

                return

            try:

                task_id = int(context.args[0])

            except ValueError:

                await update.message.reply_text(
                    'Идентификатор поручения должен быть числом.'
                )

                return

            _, message = complete_task_via_telegram(
                user,
                task_id
            )

            await update.message.reply_text(message)

        application = ApplicationBuilder().token(token).build()
        application.add_handler(CommandHandler('start', start_handler))
        application.add_handler(CommandHandler('help', help_handler))
        application.add_handler(CommandHandler('bind', bind_handler))
        application.add_handler(CommandHandler('tasks', tasks_handler))
        application.add_handler(CommandHandler('task', task_handler))

        self.stdout.write(
            self.style.SUCCESS(
                'Telegram-бот DigitalChair запущен.'
            )
        )

        application.run_polling()
