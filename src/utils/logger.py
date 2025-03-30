import logging
import os
from logging.handlers import RotatingFileHandler
from src.config.settings import LOG_CONFIG


def setup_logger():
    """Configura el sistema de logging"""
    # Crear directorio de logs si no existe
    os.makedirs("logs", exist_ok=True)

    # Configurar logging con rotación
    logging.basicConfig(
        level=getattr(logging, LOG_CONFIG["level"]),
        format=LOG_CONFIG["format"],
        handlers=[
            RotatingFileHandler(
                f"logs/{LOG_CONFIG['file']}",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Sistema de logging configurado correctamente")
