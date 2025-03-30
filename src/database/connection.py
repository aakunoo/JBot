from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from src.config.settings import DB_CONFIG
import logging
import time

logger = logging.getLogger(__name__)

# Variables globales
_client = None
_db = None
_max_retries = 3
_retry_delay = 5  # segundos


def _connect_with_retry():
    global _client, _db
    for attempt in range(_max_retries):
        try:
            _client = MongoClient(
                DB_CONFIG["uri"],
                maxPoolSize=DB_CONFIG["max_pool_size"],
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            # Verificar conexión
            _client.server_info()
            _db = _client[DB_CONFIG["database"]]
            _setup_indexes()
            logger.info("Conexión a MongoDB establecida correctamente")
            return
        except ConnectionFailure as e:
            logger.error(f"Intento {attempt + 1} fallido: {e}")
            if attempt < _max_retries - 1:
                time.sleep(_retry_delay)
            else:
                raise


def _setup_indexes():
    try:
        # Crear índices necesarios
        _db.usuarios.create_index("chat_id", unique=True)
        _db.recordatorios.create_index(
            [("chat_id", 1), ("fecha_hora_inicio", 1)])
        _db.clima.create_index([("chat_id", 1), ("provincia", 1)])
        logger.info("Índices creados correctamente")
    except OperationFailure as e:
        logger.error(f"Error al crear índices: {e}")
        raise


def get_db():
    global _client, _db
    try:
        # Verificar conexión antes de devolver
        _client.server_info()
        return _db
    except ConnectionFailure:
        logger.warning("Conexión perdida, intentando reconectar...")
        _connect_with_retry()
        return _db


# Inicializar conexión al importar el módulo
_connect_with_retry()
