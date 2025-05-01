import sys, types, pytest, mongomock
from telegram import User, Update
from types import SimpleNamespace

# ── 1. Parche global de PyMongo → mongomock ──────────────────────────
_mock_client = mongomock.MongoClient()


class _DummySession:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def start_transaction(self, *a, **k): return self
    def commit_transaction(self): pass
    def abort_transaction(self): pass
    def end_session(self): pass


_mock_client.start_session = lambda *a, **k: _DummySession()

pymongo_fake = types.ModuleType("pymongo")
pymongo_fake.MongoClient = lambda *a, **k: _mock_client
pymongo_fake.errors = types.SimpleNamespace(ServerSelectionTimeoutError=Exception)
sys.modules["pymongo"] = pymongo_fake
# ─────────────────────────────────────────────────────────────────────

# ── 2. Fixture de base de datos aislada ──────────────────────────────
@pytest.fixture()
def db(monkeypatch):
    from src.database import models
    monkeypatch.setattr(models, "db", _mock_client["jbot"])
    yield _mock_client["jbot"]
    _mock_client.drop_database("jbot")
# ─────────────────────────────────────────────────────────────────────

# ── 3. Stubs de Telegram Update + Context ────────────────────────────
async def _reply_async(*_a, **_kw):
    """Versión asíncrona de reply_text que no hace nada."""
    return None


def _fake_update(user_id: int = 1, username: str = "tester"):
    tg_user = User(id=user_id, first_name=username, is_bot=False, username=username)
    chat_stub = type("Chat", (), {"id": user_id})
    message = type(
        "Msg",
        (),
        {
            "from_user": tg_user,
            "chat": chat_stub,
            "text": "",
            "reply_text": _reply_async,
        },
    )
    return Update(update_id=999, message=message)


@pytest.fixture()
def fake_update():
    return _fake_update()


@pytest.fixture()
def fake_context():
    fake_bot = SimpleNamespace(send_message=_reply_async)
    return SimpleNamespace(bot=fake_bot, args=[])
