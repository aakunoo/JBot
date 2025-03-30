import re
from typing import Optional
from src.config.settings import SECURITY_CONFIG


def sanitize_text(text: str, max_length: int = 100) -> str:
    """Sanitiza texto de entrada"""
    if not text:
        return ""
    # Eliminar caracteres especiales y limitar longitud
    sanitized = re.sub(r'[^\w\s\-.,!?]', '', text)
    return sanitized[:max_length]


def sanitize_date(date_str: str) -> Optional[str]:
    """Sanitiza y valida fecha"""
    try:
        # Validar formato YYYY-MM-DD HH:MM
        if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', date_str):
            return None
        return date_str
    except:
        return None


def sanitize_provincia(provincia: str) -> Optional[str]:
    """Sanitiza nombre de provincia"""
    if not provincia:
        return None
    # Eliminar caracteres especiales y espacios múltiples
    sanitized = re.sub(r'[^\w\s]', '', provincia)
    sanitized = ' '.join(sanitized.split())
    return sanitized if sanitized else None
