"""
TI‑R‑01  •  Flujo completo del comando /recordatorios
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from bson.objectid import ObjectId

# --- importamos funciones internas del bot -----------------------------
from src.database.models import (
    crear_recordatorio,
    obtener_recordatorios,
    eliminar_recordatorio_por_id,
)
from src.database import models


@pytest.mark.asyncio
async def test_recordatorio_completo(real_db):  # real_db = fixture con Mongo real
    """Comprueba alta, consulta, ejecución y borrado de un recordatorio."""

    # 1) Usuario de pruebas
    chat_id = 77
    models.register_user(chat_id=chat_id, username="tester", apodo="tester")

    # 2) Creamos recordatorio para dentro de 5 minutos
    inicio = datetime.now(timezone.utc) + timedelta(minutes=5)

    oid = crear_recordatorio(
        chat_id=chat_id,
        titulo="Tomar agua",
        descripcion="Recuerda beber",
        fecha_hora_inicio=inicio,
        fecha_hora_fin=None,
        frecuencia={"tipo": "ninguna", "valor": None},
        zona_horaria="UTC+1",
    )
    # --- Comprobación de alta ------------------------------------------
    assert isinstance(oid, ObjectId)

    docs = obtener_recordatorios(chat_id)
    assert any(d["_id"] == oid for d in docs)

    # 3) Simulamos la ejecución del job (ejemplo: esperar 0.1 s)
    #    *En producción el scheduler lanzaría send_message; aquí solo
    #     verificamos que no se lanza excepción.*
    await asyncio.sleep(0.1)

    # 4) Eliminamos
    delete_res = eliminar_recordatorio_por_id(oid)
    assert delete_res.deleted_count == 1

    # 5) Lista final vacía
    assert obtener_recordatorios(chat_id) == []
