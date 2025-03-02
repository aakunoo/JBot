from telegram import Update
from telegram.ext import ContextTypes
from src.database import get_user, register_user

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
        "/clima <provincia> → Menú para saber el clima de una ciudad o gestionar tus recordatorios de clima. Si escribes una provincia junto al comando, te dirá el clima actual de esa provincia, si no, te llevará al menú."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def comando_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if get_user(chat_id):
        await update.message.reply_text("Ya estás registrado.")
        return

    nickname = " ".join(context.args) if context.args else ""
    telegram_username = update.effective_user.username

    if register_user(chat_id, telegram_username, nickname):
        display_name = nickname if nickname.strip() else telegram_username
        await update.message.reply_text(f"Registrado exitosamente como: {display_name}")
        print(f"Nuevo usuario: {display_name}, con ID de chat: {chat_id}")
    else:
        await update.message.reply_text("Error: Ya estás registrado o no se pudo registrar.")
