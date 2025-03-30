from datetime import datetime, timezone
from src.database.connection import DatabaseConnection
from src.utils.validators import validate_nickname, validate_username, validate_chat_id
from src.config.settings import SECURITY_CONFIG
import logging

logger = logging.getLogger(__name__)
db = DatabaseConnection().get_db()


class UserModel:
    @staticmethod
    def register_user(chat_id, username, apodo):
        try:
            if not all([validate_chat_id(chat_id), validate_username(username)]):
                logger.warning(
                    f"Datos de usuario inválidos: chat_id={chat_id}, username={username}")
                return False

            if not validate_nickname(apodo) and apodo:
                logger.warning(f"Apodo inválido: {apodo}")
                return False

            if db.usuarios.find_one({"chat_id": chat_id}):
                return False

            data_usuario = {
                "username": username[:SECURITY_CONFIG["max_username_length"]],
                "apodo": apodo if apodo and apodo.strip() != "" else None,
                "chat_id": chat_id,
                "registro": datetime.now(timezone.utc)
            }
            db.usuarios.insert_one(data_usuario)
            logger.info(f"Usuario registrado: {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error al registrar usuario: {e}")
            return False

    @staticmethod
    def get_user(chat_id):
        return db.usuarios.find_one({"chat_id": chat_id})

    @staticmethod
    def update_user(chat_id, data):
        return db.usuarios.update_one({"chat_id": chat_id}, {"$set": data})

    @staticmethod
    def delete_user(chat_id):
        return db.usuarios.delete_one({"chat_id": chat_id})


class ReminderModel:
    @staticmethod
    def crear_recordatorio(chat_id, titulo, descripcion, fecha_hora_inicio, frecuencia, fecha_hora_fin, zona_horaria):
        try:
            documento = {
                "chat_id": chat_id,
                "titulo": titulo,
                "descripcion": descripcion,
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
            logger.error(f"Error al crear recordatorio: {e}")
            return None

    @staticmethod
    def obtener_recordatorios(chat_id):
        return list(db.recordatorios.find({"chat_id": chat_id}))

    @staticmethod
    def eliminar_recordatorio_por_id(id_recordatorio):
        from bson.objectid import ObjectId
        return db.recordatorios.delete_one({"_id": ObjectId(id_recordatorio)})


class ClimaModel:
    @staticmethod
    def crear_suscripcion_clima(chat_id, nombre_usuario, provincia, hora_config):
        try:
            documento = {
                "chat_id": chat_id,
                "nombre_usuario": nombre_usuario,
                "provincia": provincia,
                "hora_config": hora_config,
                "creado_en": datetime.now(timezone.utc)
            }
            db.clima.insert_one(documento)
            logger.info(f"Suscripción de clima creada para usuario {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error al crear suscripción de clima: {e}")
            return False

    @staticmethod
    def obtener_recordatorios_clima(chat_id):
        return list(db.clima.find({"chat_id": chat_id}))

    @staticmethod
    def eliminar_recordatorio_clima(id_recordatorio):
        from bson.objectid import ObjectId
        return db.clima.delete_one({"_id": ObjectId(id_recordatorio)})
