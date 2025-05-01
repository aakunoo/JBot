# tests/conftest.py
import mongomock
import pytest
from telegram import User, Update
from telegram.ext import CallbackContext

# ---------- fixture de base de datos ---------- #
@pytest.fixture()
def db(monkeypatch):
    """MongoDB en memoria, sustituye al cliente real."""
    client = mongomock.MongoClient()
    from src.database import models           # se importa aquí para que exista primero el client
    monkeypatch.setattr(models, "db", client["jbot"])
    yield client["jbot"]                      # ‹return› para el test
    client.close()

# ---------- helpers de objetos Telegram ------- #
def _fake_update(user_id=1, username="tester"):
    tg_user = User(id=user_id, first_name=username, is_bot=False, username=username)
    message = type("Msg", (), {
        "from_user": tg_user,
        "text": "",
        "reply_text": lambda *_1, **_2: None,   # stub
    })
    return Update(update_id=999, message=message)

@pytest.fixture()
def fake_update():
    return _fake_update()

@pytest.fixture()
def fake_context():
    return CallbackContext.from_error(None)
