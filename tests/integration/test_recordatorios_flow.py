from datetime import datetime, timedelta, timezone
from bson.objectid import ObjectId   
from src.reminders.recordatorios import crear_recordatorio

def test_crear_recordatorio_flow(db):
    inicio = datetime.now(timezone.utc) + timedelta(hours=1)
    oid = crear_recordatorio(
        chat_id=1,
        titulo="Tomar agua",
        descripcion="Sin descripción",
        fecha_hora_inicio=inicio,
        fecha_hora_fin=None,
        frecuencia={"tipo": "ninguna", "valor": None},
        zona_horaria="UTC+1",
    )
    # ahora comprobamos que se devolvió un ObjectId válido
    assert isinstance(oid, ObjectId)

    doc = db.recordatorios.find_one({"_id": oid})
    assert doc and doc["titulo"] == "Tomar agua"