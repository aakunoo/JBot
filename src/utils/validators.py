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
    """Valida que el chat_id sea un número válido."""
    return isinstance(chat_id, int) and chat_id > 0


def validate_date(date_str: str) -> bool:
    """Valida que la fecha tenga el formato correcto."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False
