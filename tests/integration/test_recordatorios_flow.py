from datetime import datetime, timedelta
from src.reminders.recordatorios import crear_recordatorio

def test_crear_recordatorio_flow(db):
    run_at = datetime.utcnow() + timedelta(hours=1)
    ok = crear_recordatorio(chat_id=1, titulo="Tomar agua", cuando=run_at)

    assert ok is True
    doc = db.recordatorios.find_one({"chat_id": 1})
    assert doc and doc["titulo"] == "Tomar agua"
