import logging
import os
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    "uri": os.getenv("MONGO_URI"),
    "database": "jbot_db",
    "pool_size": 10,
    "max_pool_size": 50
}

# Configuración de seguridad
SECURITY_CONFIG = {
    "max_nickname_length": 50,
    "allowed_nickname_chars": r"^[a-zA-Z0-9_\- ]+$",
    "max_username_length": 32,
    "rate_limit": {
        "max_attempts": 5,
        "window_minutes": 60
    }
}

# Configuración de logging
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "bot.log"
}

# Configuración del bot
BOT_CONFIG = {
    "token": os.getenv("TELEGRAM_TOKEN"),
    "admin_ids": [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
}
