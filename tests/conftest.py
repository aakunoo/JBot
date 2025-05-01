# tests/conftest.py
import mongomock
import pytest
import types
from types import SimpleNamespace
import sys
from telegram import User, Update
from telegram.ext import CallbackContext


# 1 Crear un "MongoClient" de pruebas
_mock_client = mongomock.MongoClient()

# 2 Construir un módulo falso que imita `pymongo`
pymongo_fake = types.ModuleType("pymongo")
pymongo_fake.MongoClient = lambda *a, **k: _mock_client
pymongo_fake.errors = types.SimpleNamespace(ServerSelectionTimeoutError=Exception)
# opcionalmente:
pymongo_fake.ReturnDocument = types.SimpleNamespace(AFTER=1)

class _DummySession:
    def __enter__(self):        # with client.start_session() as s:
        return self
    def __exit__(self, exc_type, exc, tb):   # sale del with
        return False
    def start_transaction(self, *a, **k):    # no hace nada
        pass
    def commit_transaction(self):            # idem
        pass
    def abort_transaction(self):             # idem
        pass

_mock_client.start_session = lambda *a, **k: _DummySession()

# 3 Inyectar el módulo falso en `sys.modules`
sys.modules["pymongo"] = pymongo_fake

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
    """Objeto mínimo que imita telegram.ext.CallbackContext."""
    fake_bot = SimpleNamespace(send_message=lambda *a, **k: None)
    return SimpleNamespace(bot=fake_bot)