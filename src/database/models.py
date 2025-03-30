import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from src.database.connection import get_db, execute_transaction
from src.utils.validators import validate_nickname, validate_username, validate_chat_id
from src.utils.input_sanitizer import sanitize_text, sanitize_provincia
from src.utils.logger import setup_logger
from src.config.settings import BOT_CONFIG, SECURITY_CONFIG


logger = logging.getLogger(__name__)
db = get_db()


@execute_transaction
def register_user(chat_id, apodo, username=None):
    """
    Registra un nuevo usuario en la base de datos.

    Args:
        chat_id: ID del chat del usuario
        apodo: Apodo del usuario
        username: Username de Telegram del usuario (opcional)

    Returns:
        bool: True si el registro fue exitoso, False en caso contrario
    """
    try:
        if not validate_chat_id(chat_id):
            logger.warning(f"Chat ID inválido: {chat_id}")
            return False

        if db.usuarios.find_one({"chat_id": chat_id}):
            logger.info(f"Usuario ya registrado: {chat_id}")
            return False

        data_usuario = {
            "chat_id": chat_id,
            "apodo": sanitize_text(apodo),
            "username": sanitize_text(username) if username else None,
            "registro": datetime.now(timezone.utc)
        }
        db.usuarios.insert_one(data_usuario)
        logger.info(
            f"Usuario registrado: {chat_id} (apodo: {apodo}, username: {username})")
        return True
    except Exception as e:
        logger.error(f"Error al registrar usuario: {e}", exc_info=True)
        return False


@execute_transaction
def crear_recordatorio(chat_id, titulo, descripcion, fecha_hora_inicio, frecuencia, fecha_hora_fin, zona_horaria):
    try:
        documento = {
            "chat_id": chat_id,
            "titulo": sanitize_text(titulo),
            "descripcion": sanitize_text(descripcion),
            "fecha_hora_inicio": fecha_hora_inicio,
            "frecuencia": frecuencia,
            "fecha_hora_fin": fecha_hora_fin,
            "zona_horaria": zona_horaria,
            "creado_en": datetime.now(timezone.utc)
        }
        resultado = db.recordatorios.insert_one(documento)
        logger.info(f"Recordatorio creado para usuario {chat_id}")
        return resultado.inserted_id
    except Exception as e:
        logger.error(f"Error al crear recordatorio: {e}", exc_info=True)
        return None


@execute_transaction
def crear_suscripcion_clima(chat_id, nombre_usuario, provincia, hora_config):
    try:
        provincia_sanitizada = sanitize_provincia(provincia)
        if not provincia_sanitizada:
            logger.warning(f"Provincia inválida: {provincia}")
            return False

        documento = {
            "chat_id": chat_id,
            "nombre_usuario": sanitize_text(nombre_usuario),
            "provincia": provincia_sanitizada,
            "hora_config": hora_config,
            "creado_en": datetime.now(timezone.utc)
        }
        db.clima.insert_one(documento)
        logger.info(f"Suscripción de clima creada para usuario {chat_id}")
        return True
    except Exception as e:
        logger.error(
            f"Error al crear suscripción de clima: {e}", exc_info=True)
        return False


def get_user(chat_id):
    return db.usuarios.find_one({"chat_id": chat_id})


def update_user(chat_id, data):
    return db.usuarios.update_one({"chat_id": chat_id}, {"$set": data})


def delete_user(chat_id):
    return db.usuarios.delete_one({"chat_id": chat_id})


def obtener_recordatorios(chat_id=None):
    query = {"chat_id": chat_id} if chat_id is not None else {}
    return list(db.recordatorios.find(query))


def eliminar_recordatorio_por_id(id_recordatorio):
    from bson.objectid import ObjectId
    return db.recordatorios.delete_one({"_id": ObjectId(id_recordatorio)})


def obtener_recordatorios_clima(chat_id):
    return list(db.clima.find({"chat_id": chat_id}))


def eliminar_recordatorio_clima(id_recordatorio):
    from bson.objectid import ObjectId
    return db.clima.delete_one({"_id": ObjectId(id_recordatorio)})


def actualizar_recordatorio_clima(id_recordatorio, cambios):
    """
    Actualiza un recordatorio de clima existente con los cambios especificados.
    """
    from bson.objectid import ObjectId
    try:
        resultado = db.clima.update_one(
            {"_id": ObjectId(id_recordatorio)},
            {"$set": cambios}
        )
        logger.info(f"Recordatorio de clima actualizado: {id_recordatorio}")
        return resultado.modified_count > 0
    except Exception as e:
        logger.error(
            f"Error al actualizar recordatorio de clima: {e}", exc_info=True)
        return False


# Colección de clima para acceso directo
coleccion_clima = db.clima


def ajustar_hora_recordatorios_clima():
    """
    Ajusta la hora de todos los recordatorios de clima existentes
    para compensar el cambio horario.
    """
    try:
        # Obtener todos los recordatorios
        recordatorios = list(db.clima.find({}))

        for recordatorio in recordatorios:
            hora_config = recordatorio.get("hora_config", {})
            if not hora_config:
                continue

            # Ajustar la hora (restar 1 hora)
            hora_actual = hora_config.get("hora", 0)
            nueva_hora = (hora_actual - 1) % 24

            # Actualizar el recordatorio
            db.clima.update_one(
                {"_id": recordatorio["_id"]},
                {"$set": {"hora_config.hora": nueva_hora}}
            )

        logger.info("Hora de recordatorios de clima ajustada correctamente")
        return True
    except Exception as e:
        logger.error(
            f"Error al ajustar hora de recordatorios: {e}", exc_info=True)
        return False


def update_user_nickname(chat_id: int, nuevo_apodo: str) -> bool:
    """
    Actualiza el apodo de un usuario.

    Args:
        chat_id: ID del chat del usuario
        nuevo_apodo: Nuevo apodo para el usuario

    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        result = db.usuarios.update_one(
            {"chat_id": chat_id},
            {"$set": {"apodo": sanitize_text(nuevo_apodo)}}
        )
        logger.info(f"Apodo actualizado para usuario {chat_id}")
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error al actualizar apodo: {e}")
        return False
