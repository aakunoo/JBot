import os
import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler
from src.rpi.rpi_settings import get_system_info

'''
--------------------------------------------------------------------------------
comando_config
--------------------------------------------------------------------------------
'''
async def comando_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Punto de entrada para el comando /config.
    Verifica que el usuario es administrador (ADMIN_CHAT_ID) y muestra la información
    de la Raspberry PI (utilizando "uptime -p" y "ps aux") en un formato de tabla.
    """
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    logging.info(f"ADMIN_CHAT_ID: {admin_chat_id}")

    if str(chat_id).strip() != str(admin_chat_id).strip():
        await update.message.reply_text("No tienes permisos para usar este comando.")
        return ConversationHandler.END

    # Mostrar directamente la información de la Raspberry
    info = get_system_info()
    await update.message.reply_text(info)
    return ConversationHandler.END

'''
--------------------------------------------------------------------------------
get_config_handler
--------------------------------------------------------------------------------
Devuelve un ConversationHandler para el comando /config, que ahora 
muestra la información de la Raspberry sin desplegar un menú.
--------------------------------------------------------------------------------
'''
def get_config_handler():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("config", comando_config)],
        states={},
        fallbacks=[],
        per_user=True,
        per_chat=True
    )
    return conv_handler
