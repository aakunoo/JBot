import logging
from typing import Optional, Callable
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)


def handle_database_error(func: Callable) -> Callable:
    """Decorador para manejar errores de base de datos"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionFailure as e:
            logger.error(
                f"Error de conexión a la base de datos: {e}", exc_info=True)
            return None
        except OperationFailure as e:
            logger.error(
                f"Error en operación de base de datos: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(
                f"Error inesperado en base de datos: {e}", exc_info=True)
            return None
    return wrapper
