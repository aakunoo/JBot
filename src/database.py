import os
from pymongo import MongoClient
from datetime import datetime, timezone

# Cargar variable de entorno con la URI de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["jbot_db"]

# --------------------------------------------------------
# Colección de usuarios
coleccion_usuarios = db["usuarios"]

def register_user(chat_id, username, apodo):
    """
    Registra un usuario en la base de datos si aún no existe.
    :param chat_id: Id del chat (número entero).
    :param username: Username de Telegram.
    :param apodo: Nickname proporcionado o None.
    :return: True si se registró, False si ya existe.
    """
    if coleccion_usuarios.find_one({"chat_id": chat_id}):
        return False  # El usuario ya está registrado.

    data_usuario = {
        "username": username,
        "apodo": apodo if apodo and apodo.strip() != "" else None,
        "chat_id": chat_id,
        "registro": datetime.now(timezone.utc)
    }
    coleccion_usuarios.insert_one(data_usuario)
    return True

def get_user(chat_id):
    """
    Obtiene la información de un usuario registrado.
    :param chat_id: Id del chat.
    :return: Documento del usuario o None si no existe.
    """
    return coleccion_usuarios.find_one({"chat_id": chat_id})

def update_user(chat_id, data):
    """
    Actualiza la información de un usuario.
    :param chat_id: Id del chat.
    :param data: Diccionario con los campos a actualizar.
    """
    coleccion_usuarios.update_one({"chat_id": chat_id}, {"$set": data})

def delete_user(chat_id):
    """
    Elimina el registro de un usuario.
    :param chat_id: Id del chat.
    """
    coleccion_usuarios.delete_one({"chat_id": chat_id})


# --------------------------------------------------------
# Colección de recordatorios
coleccion_recordatorios = db["recordatorios"]

def crear_recordatorio(chat_id, titulo, descripcion, fecha_hora_inicio, frecuencia, fecha_hora_fin, zona_horaria):
    """
    Crea un nuevo recordatorio para un usuario.
    :param chat_id: Id del chat (debe estar registrado).
    :param titulo: Título del recordatorio.
    :param descripcion: Descripción opcional.
    :param fecha_hora_inicio: datetime con la fecha/hora de inicio.
    :param frecuencia: Diccionario con la frecuencia (ej: {"tipo": "daily", "valor": None}).
    :param fecha_hora_fin: datetime de fin (puede ser None).
    :param zona_horaria: cadena que indica la zona horaria (ej: "UTC+1", "Europe/Madrid").
    :return: El _id insertado.
    """
    documento = {
        "chat_id": chat_id,
        "titulo": titulo,
        "descripcion": descripcion,
        "fecha_hora_inicio": fecha_hora_inicio,
        "frecuencia": frecuencia,   # por ejemplo {"tipo": "every_x_days", "valor": 2}
        "fecha_hora_fin": fecha_hora_fin,
        "zona_horaria": zona_horaria,
        "creado_en": datetime.now(timezone.utc)
    }
    resultado = coleccion_recordatorios.insert_one(documento)
    return resultado.inserted_id

def obtener_recordatorios(chat_id):
    """
    Devuelve todos los recordatorios de un usuario específico.
    :param chat_id: Id del chat del usuario.
    :return: Lista de documentos de recordatorios.
    """
    return list(coleccion_recordatorios.find({"chat_id": chat_id}))

def eliminar_recordatorio_por_id(id_recordatorio):
    """
    Elimina un recordatorio por su _id.
    :param id_recordatorio: Cadena o tipo ObjectId del documento.
    :return: Resultado de la operación delete_one.
    """
    from bson.objectid import ObjectId
    return coleccion_recordatorios.delete_one({"_id": ObjectId(id_recordatorio)})

def obtener_todos_los_recordatorios():
    """
    Devuelve todos los recordatorios (de todos los usuarios).
    """
    return list(coleccion_recordatorios.find({}))


# --------------------------------------------------------
# Colección clima (Suscripciones para actualizaciones meteorológicas)
coleccion_clima = db["clima"]

def crear_suscripcion_clima(chat_id, nombre_usuario, provincia, hora_obj):
    """
    Almacena en la BBDD la suscripción de clima.
    Ejemplo de hora_obj: {"hora": 8, "minuto": 30, "zona": "UTC+1"}
    """
    documento = {
        "chat_id": chat_id,
        "nombre_usuario": nombre_usuario,
        "provincia": provincia,
        "hora_config": hora_obj,
        "creado_en": datetime.now(timezone.utc)
    }
    coleccion_clima.insert_one(documento)

def leer_suscripcion_clima(chat_id):
    """
    Ejemplo de lectura de la suscripción de un usuario (si la hubiera).
    """
    return coleccion_clima.find({"chat_id": chat_id})

def eliminar_suscripcion_clima(chat_id):
    """
    Elimina la suscripción de clima de un usuario.
    """
    return coleccion_clima.delete_many({"chat_id": chat_id})