from src.config.settings import BOT_CONFIG


def is_admin(chat_id: int) -> bool:
    """Verifica si el usuario es administrador"""
    return chat_id in BOT_CONFIG["admin_ids"]


def can_manage_reminders(chat_id: int) -> bool:
    """Verifica si el usuario puede gestionar recordatorios"""
    return True  # Por ahora todos los usuarios registrados pueden


def can_manage_clima(chat_id: int) -> bool:
    """Verifica si el usuario puede gestionar clima"""
    return True  # Por ahora todos los usuarios registrados pueden


def can_manage_system(chat_id: int) -> bool:
    """Verifica si el usuario puede gestionar el sistema"""
    return is_admin(chat_id)
