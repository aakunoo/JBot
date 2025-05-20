from telegram import Update
from telegram.ext import ContextTypes
from src.database.models import register_user, get_user, update_user_nickname
from src.core.security import validate_nickname, is_rate_limited, record_attempt
from src.utils.input_sanitizer import sanitize_text
from src.utils.validators import validate_chat_id, validate_username, validar_apodo
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
            "/register <apodo> → Para registrarte. Obligatorio el uso de un apodo.\n\n"
            "*Comandos accesibles sólo para usuarios registrados:*\n"
            "----------------------------------------------------------------------------------\n"
            "/setnickname <apodo> → Para cambiar tu apodo.\n"
            "/recordatorios → Menú para gestionar recordatorios.\n"
            "/clima <provincia> → Menú para saber el clima de una ciudad o gestionar tus recordatorios de clima.\n\n"
            "*Comandos accesibles sólo para administradores:*\n"
            "----------------------------------------------------------------------------------\n"
            "/config → INFO de la Raspberry Pi.\n"
            "----------------------------------------------------------------------------------\n"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
        logger.info(f"Usuario {update.effective_user.id} solicitó ayuda")
    except Exception as e:
        logger.error(f"Error en comando help: {e}", exc_info=True)
        await update.message.reply_text("Lo siento, ha ocurrido un error. Por favor, intenta más tarde.")


async def comando_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el comando /register.
    Si no se proporciona un apodo, solicita al usuario que lo introduzca.
    """
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = get_user(user_id)

    if user:
        await update.message.reply_text(
            "Ya estás registrado. Si quieres cambiar tu apodo, usa el comando /setnickname <nuevo_apodo>"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Por favor, introduce un apodo después del comando /register.\n"
            "Ejemplo: /register mi_apodo\n\n"
            "Reglas para el apodo:\n"
            "- Debe tener entre 2 y 15 caracteres\n"
            "- Solo puede contener letras, números y guiones bajos\n"
            "- No puede contener espacios"
        )
        return

    apodo = context.args[0]
    es_valido, mensaje_error = validar_apodo(apodo)

    if not es_valido:
        await update.message.reply_text(f"Error: {mensaje_error}")
        return

    # Obtener el username de Telegram
    telegram_username = update.effective_user.username if update.effective_user else None

    # Registrar usuario
    if register_user(chat_id, user_id, apodo, telegram_username):
        await update.message.reply_text(
            f"¡Registro exitoso! Tu apodo es: {apodo}\n"
            "Puedes cambiarlo en cualquier momento usando /setnickname <nuevo_apodo>"
        )
    else:
        await update.message.reply_text("Error al registrar el usuario. Por favor, intenta de nuevo.")


async def comando_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el comando /setnickname para cambiar el apodo del usuario.
    """
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user = get_user(user_id)

        if not user:
            await update.message.reply_text(
                "No estás registrado. Por favor, usa primero el comando /register <apodo>"
            )
            return

        if not context.args:
            await update.message.reply_text(
                "Por favor, introduce un nuevo apodo después del comando /setnickname.\n"
                "Ejemplo: /setnickname mi_nuevo_apodo\n\n"
                "Reglas para el apodo:\n"
                "- Debe tener entre 2 y 15 caracteres\n"
                "- Solo puede contener letras, números y guiones bajos\n"
                "- No puede contener espacios"
            )
            return

        nuevo_apodo = context.args[0]
        es_valido, mensaje_error = validar_apodo(nuevo_apodo)

        if not es_valido:
            await update.message.reply_text(f"Error: {mensaje_error}")
            return
        if update_user_nickname(user_id, nuevo_apodo):
            await update.message.reply_text(f"¡Apodo actualizado! Tu nuevo apodo es: {nuevo_apodo}")
        else:
            await update.message.reply_text("Error al actualizar el apodo. Por favor, intenta de nuevo.")

    except Exception as e:
        logger.error(f"Error en comando nickname: {e}", exc_info=True)
        await update.message.reply_text("Lo siento, ha ocurrido un error. Por favor, intenta más tarde.")
