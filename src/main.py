import os
from dotenv import load_dotenv
load_dotenv() # Cargamos las variables de entorno (TOKEN, MONGO_URI, etc.)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler, CallbackQueryHandler
)
from src.comandos_bot import comando_start, comando_help, comando_registro
from src.reminders.recordatorios import conv_handler_recordatorios
from src.reminders.mensaje_recordatorios import reprogramar_todos_los_recordatorios
from src.reminders.gestion_recordatorios import procesar_eliminar_recordatorio


def main():
    token = os.getenv("TELEGRAM_TOKEN")

    async def error_handler(update, context):
        print("Ocurrió un error:", context.error)


    app = ApplicationBuilder().token(token).build()

    app.job_queue.run_once(iniciar_reprogramado, when=0)
    app.add_error_handler(error_handler)

    # Handlers de comandos básicos
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(CommandHandler("help", comando_help))
    app.add_handler(CommandHandler("register", comando_registro))
    app.add_handler(conv_handler_recordatorios)
    app.add_handler(CallbackQueryHandler(procesar_eliminar_recordatorio, pattern="^eliminar_"))

    print("Bot en funcionamiento...")
    app.run_polling()


async def iniciar_reprogramado(context):
    await reprogramar_todos_los_recordatorios(context)

async def error_handler(update, context):
    print("Ocurrió un error:", context.error)


if __name__ == "__main__":
    main()
