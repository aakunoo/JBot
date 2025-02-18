import os
from dotenv import load_dotenv
load_dotenv() # Cargo primero las variables de entorno antes de importar database.py para que me identifique bien la url de la BBDD.
from telegram.ext import ApplicationBuilder, CommandHandler
from database import register_user, get_user

def main():

    # Leer el token
    token = os.getenv("TELEGRAM_TOKEN")

    # Crear la aplicación
    app = ApplicationBuilder().token(token).build()

    # Definir las funciones para los comandos
    async def start(update, context):
        await update.message.reply_text("Hola! Bienvenido a JBot. \nUsa /help para ver la lista de comandos disponibles.")

    async def registro(update, context):
        chat_id = update.effective_chat.id

        # Comprobar si el usuario ya está registrado
        if get_user(chat_id):
            await update.message.reply_text("Ya estás registrado.")
            return

        # Obtener el nickname proporcionado (si existe)
        nickname = " ".join(context.args) if context.args else ""

        # Si no se introduce nickname, se usará el username de Telegram (pero en la base se guardará null para el campo apodo)
        telegram_username = update.effective_user.username

        # Intentar registrar el usuario
        if register_user(chat_id, telegram_username, nickname):
            # Si se proporcionó un nickname, se usa; si no, se usa el username
            display_name = nickname if nickname.strip() != "" else telegram_username
            await update.message.reply_text(f"Registrado exitosamente como: {display_name}")
        else:
            await update.message.reply_text("Error: Ya estás registrado o no se pudo registrar.")


    async def comando_help(update, context):
        await update.message.reply_text("Comandos disponibles: \n- /register xxxx → Para registrarte y tener acceso al resto de comandos. \n\n xxxx Equivale al nickname. Si no indicas nada se usará tu username de Telegram por defecto. ")

    # Registrar los comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", comando_help))
    app.add_handler(CommandHandler("register", registro))

    # Iniciar el bot
    app.run_polling()


if __name__ == "__main__":
    main()
