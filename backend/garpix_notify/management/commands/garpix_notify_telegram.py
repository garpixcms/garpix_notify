from django.core.management.base import BaseCommand
from telegram import Update
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from garpix_notify.models.config import NotifyConfig
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

@sync_to_async
def get_notify_config():
    return NotifyConfig.get_solo().__dict__

@sync_to_async
def update_user_telegram_chat_id(telegram_secret, telegram_chat_id):
    count = User.objects.filter(telegram_secret=telegram_secret).update(telegram_chat_id=telegram_chat_id)
    return count

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = await get_notify_config()
    await update.message.reply_text(config['telegram_help_text'])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = await get_notify_config()
    await update.message.reply_text(config['telegram_welcome_text'])
    await update.message.reply_text(config['telegram_help_text'])

async def command_set_key(update, context):
    config = await get_notify_config()
    telegram_secret = context.args[0]
    count = await update_user_telegram_chat_id(telegram_secret, update.message.chat_id)
    if count == 1:
        await update.message.reply_text(config['telegram_success_added_text'])
    else:
        await update.message.reply_text(config['telegram_failed_added_text'])

class Command(BaseCommand):
    help = 'Starts the Telegram bot'

    def handle(self, *args, **kwargs):
        notify_config = NotifyConfig.get_solo()
        token = notify_config.telegram_api_key

        app = ApplicationBuilder().token(token).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler('set', command_set_key))
        app.add_handler(CommandHandler('help', show_help))

        app.run_polling()
