from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError
from src.config.settings import DB_CONFIG
import logging
import time
import atexit

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
            if _client:
                _client.close()

            _client = MongoClient(
                DB_CONFIG["uri"],
                maxPoolSize=DB_CONFIG["max_pool_size"],
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                retryWrites=True,
                w='majority'
            )
            # Verificar conexión
            _client.server_info()
            _db = _client[DB_CONFIG["database"]]
            _setup_indexes()
            logger.info("Conexión a MongoDB establecida correctamente")
            return
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Intento {attempt + 1} fallido: {e}")
            if attempt < _max_retries - 1:
                time.sleep(_retry_delay)
            else:
                raise


def _setup_indexes():
    try:
        # Crear índices necesarios
        _db.usuarios.create_index("user_id", unique=True)
        _db.recordatorios.create_index(
            [("user_id", 1), ("fecha_hora_inicio", 1)])
        _db.clima.create_index([("user_id", 1), ("provincia", 1)])
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
    except (ConnectionFailure, ServerSelectionTimeoutError, AttributeError):
        logger.warning(
            "Conexión perdida o no inicializada, intentando reconectar...")
        _connect_with_retry()
        return _db


def close_connection():
    global _client
    if _client:
        try:
            _client.close()
            logger.info("Conexión a MongoDB cerrada")
        except Exception as e:
            logger.error(f"Error al cerrar conexión: {e}")


# Registrar función de cierre
atexit.register(close_connection)

# Inicializar conexión al importar el módulo
_connect_with_retry()


def execute_transaction(func):
    """Decorador para ejecutar operaciones en transacciones"""
    def wrapper(*args, **kwargs):
        session = _client.start_session()
        try:
            with session.start_transaction():
                result = func(*args, **kwargs)
                session.commit_transaction()
                return result
        except Exception as e:
            session.abort_transaction()
            raise
        finally:
            session.end_session()
    return wrapper
