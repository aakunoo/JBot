from src.database import models

def test_register_user_new(db):
    ok = models.register_user(chat_id=111, nombre="Ana", username="anaTG")
    assert ok is True
    assert db.usuarios.count_documents({}) == 1

def test_register_user_duplicate(db):
    models.register_user(222, "Bob")
    ok = models.register_user(222, "Bob")
    assert ok is False

def test_update_nickname(db):
    models.register_user(333, "Carlos")
    ok = models.update_user_nickname(333, "Charlie")
    user = db.usuarios.find_one({"chat_id": 333})
    assert ok is True and user["nickname"] == "Charlie"
