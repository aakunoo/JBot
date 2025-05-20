from datetime import datetime, timedelta
from collections import defaultdict
import re
from src.config.settings import SECURITY_CONFIG
from src.database.models import get_user
from src.utils.logger import setup_logger
import logging
from telegram import Update

from src.core.permissions import can_manage_system

logger = logging.getLogger(__name__)

# Variable global para almacenar los intentos
_attempts = defaultdict(list)


def validate_nickname(nickname: str) -> bool:
    if not nickname:
        return False
    if len(nickname) > SECURITY_CONFIG["max_nickname_length"]:
        return False
    return bool(re.match(SECURITY_CONFIG["allowed_nickname_chars"], nickname))


def is_rate_limited(chat_id: int) -> bool:
    now = datetime.now()
    _attempts[chat_id] = [t for t in _attempts[chat_id]
                          if now - t < timedelta(minutes=SECURITY_CONFIG["rate_limit"]["window_minutes"])]
    return len(_attempts[chat_id]) >= SECURITY_CONFIG["rate_limit"]["max_attempts"]


def record_attempt(chat_id: int):
    _attempts[chat_id].append(datetime.now())
    logger.debug(f"Intento registrado para chat_id {chat_id}")


def check_command_permissions(update: Update, command: str) -> bool:
    """Verifica si el usuario tiene permisos para ejecutar un comando"""
    user_id = update.effective_user.id
    
    # Comandos públicos que no requieren registro
    if command in ["/start", "/help", "/register"]:
        return True
        
    # Verificar si el usuario está registrado
    if not get_user(user_id):
        return False
        
    # Comandos para usuarios registrados
    if command in ["/clima", "/recordatorios", "/setnickname"]:
        return True
        
    # Comandos solo para administradores
    if command in ["/config"]:
        return is_admin(user_id)
        
    return False


def check_rate_limit(chat_id: int, command: str) -> bool:
    """Verifica si el usuario ha excedido el límite de comandos"""
    # Implementar lógica de rate limiting por comando
    pass
