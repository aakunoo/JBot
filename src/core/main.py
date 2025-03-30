import logging
import signal
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from src.core.commands import comando_start, comando_help, comando_registro
from src.reminders.recordatorios import conv_handler_recordatorios
from src.reminders.mensaje_recordatorios import reprogramar_todos_los_recordatorios
from src.reminders.gestion_recordatorios import procesar_eliminar_recordatorio
from src.clima.clima_bot import conv_handler_clima
from src.rpi.rpi_settings import get_system_info
from src.rpi.rpi_config import get_config_handler
from src.config.settings import BOT_CONFIG, LOG_CONFIG
from src.utils.logger import setup_logger
from src.database.models import ajustar_hora_recordatorios_clima

# Configurar logging
setup_logger()
logger = logging.getLogger(__name__)


def main():
    def signal_handler(signum, frame):
        logger.info("Señal de terminación recibida. Cerrando bot...")
        app.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Ajustar hora de recordatorios existentes
        ajustar_hora_recordatorios_clima()

        app = ApplicationBuilder().token(BOT_CONFIG["token"]).build()

        # Reprogramar recordatorios existentes al arrancar el bot
        app.job_queue.run_once(iniciar_reprogramado, when=0)
        app.add_error_handler(error_handler)

        # Handlers de comandos básicos
        app.add_handler(CommandHandler("start", comando_start))
        app.add_handler(CommandHandler("help", comando_help))
        app.add_handler(CommandHandler("register", comando_registro))

        # Handler para recordatorios
        app.add_handler(conv_handler_recordatorios)
        app.add_handler(CallbackQueryHandler(
            procesar_eliminar_recordatorio, pattern="^eliminar_"))

        # Handler para el comando /clima
        app.add_handler(conv_handler_clima)

        # Handler para el comando /RSettings
        app.add_handler(get_config_handler())

        logger.info("Bot iniciado correctamente")
        app.run_polling()

    except Exception as e:
        logger.error(f"Error fatal en el bot: {e}", exc_info=True)
        raise


async def error_handler(update, context):
    logger.error(f"Error en el bot: {context.error}", exc_info=True)
    if update:
        logger.error(f"Update que causó el error: {update}")


async def iniciar_reprogramado(context):
    await reprogramar_todos_los_recordatorios(context)

if __name__ == "__main__":
    main()
