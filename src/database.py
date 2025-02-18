import os
from pymongo import MongoClient
from datetime import datetime, timezone

# Conexión a MongoDB local en la Raspberry
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["jbot_db"]  # Nombre de la base de datos
users_collection = db["usuarios"]  # Nombre de la colección


def register_user(chat_id, username, apodo):
    """
    Registra un usuario en la base de datos si aún no existe.
    :param chat_id: Id del chat (número entero).
    :param username: Username de Telegram.
    :param apodo: Nickname proporcionado o None.
    :return: True si se registró, False si ya existe.
    """
    if users_collection.find_one({"chat_id": chat_id}):
        return False  # El usuario ya está registrado.

    user_data = {
        "username": username,
        "apodo": apodo if apodo and apodo.strip() != "" else None,
        "chat_id": chat_id,
        "registro": datetime.now(timezone.utc)
    }
    users_collection.insert_one(user_data)
    return True


def get_user(chat_id):
    """
    Obtiene la información de un usuario registrado.
    :param chat_id: Id del chat.
    :return: Documento del usuario o None si no existe.
    """
    return users_collection.find_one({"chat_id": chat_id})


def update_user(chat_id, data):
    """
    Actualiza la información de un usuario.
    :param chat_id: Id del chat.
    :param data: Diccionario con los campos a actualizar.
    """
    users_collection.update_one({"chat_id": chat_id}, {"$set": data})


def delete_user(chat_id):
    """
    Elimina el registro de un usuario.
    :param chat_id: Id del chat.
    """
    users_collection.delete_one({"chat_id": chat_id})
