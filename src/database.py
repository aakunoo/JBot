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
    '''
    Función que registra un nuevo usuario en la base de datos,
    almacenando su chat_id, username y un posible apodo. Devuelve
    False si el usuario ya estaba registrado.
    '''
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
    '''
    Función que retorna el documento correspondiente a un usuario,
    encontrándolo por chat_id. Devuelve None si no existe.
    '''
    return coleccion_usuarios.find_one({"chat_id": chat_id})

def update_user(chat_id, data):
    '''
    Función para actualizar campos específicos de un usuario,
    por medio de un diccionario de cambios (data).
    '''
    coleccion_usuarios.update_one({"chat_id": chat_id}, {"$set": data})


def delete_user(chat_id):
    '''
    Función para eliminar completamente el registro de un usuario,
    ubicado por su chat_id.
    '''
    coleccion_usuarios.delete_one({"chat_id": chat_id})

# --------------------------------------------------------
# Colección de recordatorios
coleccion_recordatorios = db["recordatorios"]



def crear_recordatorio(chat_id, titulo, descripcion, fecha_hora_inicio, frecuencia, fecha_hora_fin, zona_horaria):
    '''
    Crea un nuevo recordatorio en la colección "recordatorios",
    retornando el _id insertado.
    '''
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
    '''
    Devuelve una lista de todos los recordatorios que pertenezcan
    al chat_id especificado.
    '''
    return list(coleccion_recordatorios.find({"chat_id": chat_id}))


def eliminar_recordatorio_por_id(id_recordatorio):
    '''
    Elimina un recordatorio buscándolo por su ObjectId,
    y retorna el resultado de la operación delete_one.
    '''
    from bson.objectid import ObjectId
    return coleccion_recordatorios.delete_one({"_id": ObjectId(id_recordatorio)})


def obtener_todos_los_recordatorios():
    '''
    Devuelve todos los recordatorios existentes (de todos los usuarios).
    Se usa, por ejemplo, para reprogramar todo al iniciar.
    '''
    return list(coleccion_recordatorios.find({}))


# --------------------------------------------------------
# Colección clima (Suscripciones para actualizaciones meteorológicas)
# Colección clima (Suscripciones / recordatorios de clima)
coleccion_clima = db["clima"]


def crear_suscripcion_clima(chat_id, nombre_usuario, provincia, hora_config):
    '''
    Crea una suscripción (recordatorio) de clima en la colección "clima",
    asociando un chat_id y datos de hora_config (hora, minuto, zona),
    junto a la provincia y el nombre de usuario.
    '''
    documento = {
        "chat_id": chat_id,
        "nombre_usuario": nombre_usuario,
        "provincia": provincia,
        "hora_config": hora_config,  # {"hora":8, "minuto":30, "zona":"UTC+1"}
        "creado_en": datetime.now(timezone.utc)
    }
    coleccion_clima.insert_one(documento)


def obtener_recordatorios_clima(chat_id):
    '''
    Devuelve todos los recordatorios de clima para un chat_id concreto,
    como lista de documentos.
    '''
    return list(coleccion_clima.find({"chat_id": chat_id}))


def eliminar_recordatorio_clima(id_recordatorio):
    '''
    Elimina un recordatorio de clima buscándolo por su ObjectId.
    '''
    from bson.objectid import ObjectId
    return coleccion_clima.delete_one({"_id": ObjectId(id_recordatorio)})


def actualizar_recordatorio_clima(id_recordatorio, cambios):
    '''
    Actualiza un recordatorio de clima, identificándolo por su id_recordatorio,
    y aplicando un diccionario de cambios (por ejemplo la nueva hora_config).
    '''
    from bson.objectid import ObjectId
    return coleccion_clima.update_one({"_id": ObjectId(id_recordatorio)}, {"$set": cambios})