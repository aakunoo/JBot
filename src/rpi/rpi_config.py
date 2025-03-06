import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
from src.rpi.rpi_settings import get_system_info

''' 
--------------------------------------------------------------------------------
comando_config
--------------------------------------------------------------------------------
'''
async def comando_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Punto de entrada para el comando /config.
    Solo el administrador (definido en ADMIN_CHAT_ID) puede usar este comando.
    Muestra un menú de dos opciones:
      - "Ver información de la Raspberry": Muestra datos básicos de la Raspberry PI 4.
      - "Ver información del dispositivo actual": Opción en desarrollo.
    """
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID: {chat_id}")
    logging.info(f"ADMIN_CHAT_ID: {admin_chat_id}")

    if str(chat_id) != str(admin_chat_id):
        await update.message.reply_text("No tienes permisos para usar este comando.")
        return ConversationHandler.END

    # Crear teclado con dos botones, aclarando que son opciones de configuración del clima
    botones = [
        [InlineKeyboardButton("Ver información de la Raspberry", callback_data="config_raspberry")],
        [InlineKeyboardButton("Ver información del dispositivo actual", callback_data="config_dispositivo")]
    ]
    teclado = InlineKeyboardMarkup(botones)
    await update.message.reply_text("Elige una opción de configuración:", reply_markup=teclado)
    return 0

''' 
--------------------------------------------------------------------------------
callback_config
--------------------------------------------------------------------------------
'''
async def callback_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback que procesa la selección en el menú del comando /config.
    - Si se selecciona "config_raspberry", se obtiene la información del sistema (de la Raspberry PI).
    - Si se selecciona "config_dispositivo", se notifica que la opción está en desarrollo.
    """
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "config_raspberry":
        # Obtenemos la información del sistema de la Raspberry
        info = get_system_info()
        await query.edit_message_text(info)
    elif data == "config_dispositivo":
        await query.edit_message_text("La opción 'Información del dispositivo actual' está en desarrollo.")
    else:
        await query.edit_message_text("Opción no reconocida.")
    return ConversationHandler.END

''' 
--------------------------------------------------------------------------------
get_config_handler
--------------------------------------------------------------------------------
Devuelve un ConversationHandler para el comando /config.
--------------------------------------------------------------------------------
'''
def get_config_handler():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("config", comando_config)],
        states={
            0: [CallbackQueryHandler(callback_config, pattern="^(config_raspberry|config_dispositivo)$")]
        },
        fallbacks=[],
        per_user=True,
        per_chat=True
    )
    return conv_handler
