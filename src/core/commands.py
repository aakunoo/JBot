from telegram import Update
from telegram.ext import ContextTypes
from src.database.models import register_user, get_user
from src.core.security import validate_nickname, is_rate_limited, record_attempt
from src.utils.input_sanitizer import sanitize_text
from src.utils.validators import validate_chat_id, validate_username
from src.utils.logger import setup_logger
import logging

logger = logging.getLogger(__name__)


async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start"""
    try:
        await update.message.reply_text(
            "¡Hola! Bienvenido a JBot.\nUsa /help para ver la lista de comandos disponibles."
        )
        logger.info(f"Usuario {update.effective_user.id} inició el bot")
    except Exception as e:
        logger.error(f"Error en comando start: {e}", exc_info=True)
        await update.message.reply_text("Lo siento, ha ocurrido un error. Por favor, intenta más tarde.")


async def comando_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /help"""
    try:
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
        logger.info(f"Usuario {update.effective_user.id} solicitó ayuda")
    except Exception as e:
        logger.error(f"Error en comando help: {e}", exc_info=True)
        await update.message.reply_text("Lo siento, ha ocurrido un error. Por favor, intenta más tarde.")


async def comando_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /register"""
    try:
        chat_id = update.effective_chat.id

        # Verificar rate limiting
        if is_rate_limited(chat_id):
            logger.warning(
                f"Usuario {chat_id} excedió el límite de intentos de registro")
            await update.message.reply_text("Has excedido el límite de intentos. Por favor, espera un momento.")
            return

        # Verificar si ya está registrado
        if get_user(chat_id):
            logger.info(f"Usuario {chat_id} ya está registrado")
            await update.message.reply_text("Ya estás registrado.")
            return

        # Obtener y validar datos
        nickname = " ".join(context.args) if context.args else ""
        telegram_username = update.effective_user.username

        # Validar y sanitizar datos
        if not validate_chat_id(chat_id):
            logger.warning(f"Chat ID inválido: {chat_id}")
            await update.message.reply_text("Error: ID de chat inválido.")
            return

        if not validate_username(telegram_username):
            logger.warning(f"Username inválido: {telegram_username}")
            await update.message.reply_text("Error: Username inválido.")
            return

        if nickname and not validate_nickname(nickname):
            logger.warning(f"Nickname inválido: {nickname}")
            await update.message.reply_text("El apodo contiene caracteres no permitidos.")
            return

        # Sanitizar datos
        sanitized_username = sanitize_text(telegram_username[:32])
        sanitized_nickname = sanitize_text(nickname) if nickname else None

        # Registrar usuario
        if register_user(chat_id, sanitized_username, sanitized_nickname):
            display_name = sanitized_nickname if sanitized_nickname else sanitized_username
            await update.message.reply_text(f"Registrado exitosamente como: {display_name}")
            logger.info(
                f"Nuevo usuario registrado: {display_name} (ID: {chat_id})")
        else:
            await update.message.reply_text("Error: No se pudo completar el registro.")
            logger.error(f"Error al registrar usuario {chat_id}")

        # Registrar intento
        record_attempt(chat_id)

    except Exception as e:
        logger.error(f"Error en comando registro: {e}", exc_info=True)
        await update.message.reply_text("Lo siento, ha ocurrido un error. Por favor, intenta más tarde.")
