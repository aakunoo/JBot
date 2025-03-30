from datetime import datetime, timedelta
from collections import defaultdict
import re
from src.config.settings import SECURITY_CONFIG
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    def __init__(self):
        self.attempts = defaultdict(list)

    def validate_nickname(self, nickname: str) -> bool:
        if not nickname:
            return False
        if len(nickname) > SECURITY_CONFIG["max_nickname_length"]:
            return False
        return bool(re.match(SECURITY_CONFIG["allowed_nickname_chars"], nickname))

    def is_rate_limited(self, chat_id: int) -> bool:
        now = datetime.now()
        self.attempts[chat_id] = [t for t in self.attempts[chat_id]
                                  if now - t < timedelta(minutes=SECURITY_CONFIG["rate_limit"]["window_minutes"])]
        return len(self.attempts[chat_id]) >= SECURITY_CONFIG["rate_limit"]["max_attempts"]

    def record_attempt(self, chat_id: int):
        self.attempts[chat_id].append(datetime.now())
        logger.debug(f"Intento registrado para chat_id {chat_id}")
