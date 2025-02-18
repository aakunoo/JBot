import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler


def main():
    # Cargar variables de entorno desde .env
    load_dotenv()

    # Leer el token
    token = os.getenv("TELEGRAM_TOKEN")

    # Crear la aplicación (en python-telegram-bot v20+ se usa ApplicationBuilder)
    app = ApplicationBuilder().token(token).build()

    # Definir las funciones para los comandos
    async def start(update, context):
        await update.message.reply_text("Hola! Bienvenido a JBot.")

    async def help_command(update, context):
        await update.message.reply_text("En desarrollo.")

    # Registrar los comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Iniciar el bot
    print("Bot en funcionamiento.")
    app.run_polling()


if __name__ == "__main__":
    main()
