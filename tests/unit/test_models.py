from datetime import datetime
from src.database import models

def test_register_user_new(db):
    ok = models.register_user(chat_id=111, username="anaTG", apodo="ana")
    assert ok is True
    doc = db.usuarios.find_one({"chat_id": 111})
    assert doc["username"] == "anaTG" and doc["apodo"] == "ana"

def test_register_user_duplicate(db):
    models.register_user(chat_id=222, username="bobTG", apodo="bob")
    ok = models.register_user(chat_id=222, username="bobTG", apodo="bob")
    assert ok is False

def test_update_nickname(db):
    models.register_user(chat_id=333, username="carlosTG", apodo="carlos")
    ok = models.update_user_nickname(333, "Charlie")
    doc = db.usuarios.find_one({"chat_id": 333})
    assert ok is True and doc["apodo"] == "Charlie"
