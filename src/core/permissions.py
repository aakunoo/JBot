from src.config.settings import BOT_CONFIG
from src.utils.logger import setup_logger
import logging

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """
    Verifica si el usuario es administrador.
    Los administradores están definidos en BOT_CONFIG["admin_ids"]
    """
    try:
        return user_id in BOT_CONFIG["admin_ids"]
    except Exception as e:
        logger.error(f"Error al verificar permisos de administrador: {e}")
        return False


def can_manage_reminders(user_id: int) -> bool:
    """Verifica si el usuario puede gestionar recordatorios"""
    return True  # Por ahora todos los usuarios registrados pueden


def can_manage_clima(user_id: int) -> bool:
    """Verifica si el usuario puede gestionar clima"""
    return True  # Por ahora todos los usuarios registrados pueden


def can_manage_system(user_id: int) -> bool:
    """Verifica si el usuario puede gestionar el sistema"""
    return is_admin(user_id)
