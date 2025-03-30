from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from src.config.settings import DB_CONFIG
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            self.client = MongoClient(
                DB_CONFIG["uri"],
                maxPoolSize=DB_CONFIG["max_pool_size"],
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[DB_CONFIG["database"]]
            self._setup_indexes()
            logger.info("Conexión a MongoDB establecida correctamente")
        except ConnectionFailure as e:
            logger.error(f"Error al conectar con MongoDB: {e}")
            raise

    def _setup_indexes(self):
        # Crear índices necesarios
        self.db.usuarios.create_index("chat_id", unique=True)
        self.db.recordatorios.create_index(
            [("chat_id", 1), ("fecha_hora_inicio", 1)])
        self.db.clima.create_index([("chat_id", 1), ("provincia", 1)])

    def get_db(self):
        return self.db
