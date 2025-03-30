from telegram import Update
from telegram.ext import ContextTypes
from src.database.models import UserModel
from src.core.security import SecurityManager
from src.utils.validators import validate_nickname
import logging

logger = logging.getLogger(__name__)
security = SecurityManager()


async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Bienvenido a JBot.\nUsa /help para ver la lista de comandos disponibles."
    )


async def comando_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*Comandos disponibles:*\n\n"
        "*Registro:*\n"
        "/register <apodo> → Para registrarte. Si no indicas nada, se usará tu username.\n\n"
        "*Comandos accesibles sólo para usuarios registrados:*\n"
        "-----------------------------------------------------------------------------------\n"
        "/recordatorios → Menú para gestionar recordatorios.\n"
        "/clima <provincia> → Menú para saber el clima de una ciudad o gestionar tus recordatorios de clima."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def comando_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if security.is_rate_limited(chat_id):
        await update.message.reply_text("Has excedido el límite de intentos. Por favor, espera un momento.")
        return

    if UserModel.get_user(chat_id):
        await update.message.reply_text("Ya estás registrado.")
        return

    nickname = " ".join(context.args) if context.args else ""
    telegram_username = update.effective_user.username

    if not validate_nickname(nickname) and nickname:
        await update.message.reply_text("El apodo contiene caracteres no permitidos.")
        return

    if UserModel.register_user(chat_id, telegram_username, nickname):
        display_name = nickname if nickname.strip() else telegram_username
        await update.message.reply_text(f"Registrado exitosamente como: {display_name}")
        logger.info(
            f"Nuevo usuario: {display_name}, con ID de chat: {chat_id}")
    else:
        await update.message.reply_text("Error: Ya estás registrado o no se pudo registrar.")

    security.record_attempt(chat_id)
