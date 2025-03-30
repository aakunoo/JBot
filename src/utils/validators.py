import re
from datetime import datetime
from src.config.settings import SECURITY_CONFIG


def validate_nickname(nickname: str) -> bool:
    """Valida que el nickname cumpla con los requisitos de seguridad."""
    if not nickname:
        return False
    if len(nickname) > SECURITY_CONFIG["max_nickname_length"]:
        return False
    return bool(re.match(SECURITY_CONFIG["allowed_nickname_chars"], nickname))


def validate_username(username: str) -> bool:
    """Valida que el username cumpla con los requisitos de seguridad."""
    if not username:
        return False
    if len(username) > SECURITY_CONFIG["max_username_length"]:
        return False
    return True


def validate_chat_id(chat_id: int) -> bool:
    """
    Valida que el chat_id sea un número entero positivo.

    Args:
        chat_id: ID del chat a validar

    Returns:
        bool: True si el chat_id es válido, False en caso contrario
    """
    try:
        return isinstance(chat_id, int) and chat_id > 0
    except Exception:
        return False


def validate_date(date_str: str) -> bool:
    """Valida que la fecha tenga el formato correcto."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def validar_apodo(apodo: str) -> tuple[bool, str]:
    """
    Valida un apodo según las siguientes reglas:
    - Longitud entre 2 y 15 caracteres
    - No puede contener caracteres especiales
    - No puede contener espacios

    Returns:
        tuple[bool, str]: (es_válido, mensaje_error)
    """
    if not apodo:
        return False, "El apodo no puede estar vacío."

    if len(apodo) < 2:
        return False, "El apodo debe tener al menos 2 caracteres."

    if len(apodo) > 15:
        return False, "El apodo no puede tener más de 15 caracteres."

    if not apodo.replace('_', '').isalnum():
        return False, "El apodo solo puede contener letras, números y guiones bajos."

    if ' ' in apodo:
        return False, "El apodo no puede contener espacios."

    return True, ""
