from django.core.management.base import BaseCommand
from telegram.ext import Updater, CommandHandler
from ...models.config import NotifyConfig
from django.contrib.auth import get_user_model


def required_argument(fn):
    def wrapper(update, context):
        config = NotifyConfig.get_solo()
        if int(len(context.args)) == 0:
            update.message.reply_text(config.telegram_bad_command_text)
            return False
        return fn(update, context)

    return wrapper


def start(update, context):
    config = NotifyConfig.get_solo()
    update.message.reply_text(config.telegram_welcome_text)
    update.message.reply_text(config.telegram_help_text)


def show_help(update, context):
    config = NotifyConfig.get_solo()
    update.message.reply_text(config.telegram_help_text)


@required_argument
def command_set_key(update, context):
    config = NotifyConfig.get_solo()
    telegram_secret = context.args[0]
    User = get_user_model()
    user = User.objects.filter(telegram_secret=telegram_secret).first()
    if user is not None:
        user.telegram_chat_id = update.message.chat_id
        user.save()
        update.message.reply_text(config.telegram_success_added_text)
    else:
        update.message.reply_text(config.telegram_failed_added_text)


class Command(BaseCommand):
    help = 'Telegram garpix_notify daemon.'

    def handle(self, *args, **options):
        notify_config = NotifyConfig.get_solo()
        updater = Updater(notify_config.telegram_api_key)
        updater.dispatcher.add_handler(CommandHandler('start', start))
        updater.dispatcher.add_handler(CommandHandler('set', command_set_key, pass_args=True))
        updater.dispatcher.add_handler(CommandHandler('help', show_help))
        updater.start_polling()
        updater.idle()
