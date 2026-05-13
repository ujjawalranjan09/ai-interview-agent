"""Database connection module with MongoDB singleton, retry logic, and connection pooling."""

import logging
import time
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import MONGO_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY = 1.5  # seconds; doubles each attempt


class MongoDBConnection:
    """MongoDB connection singleton with retry logic and connection pooling."""

    _instance: Optional["MongoDBConnection"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls) -> "MongoDBConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> None:
        """Establish MongoDB connection with exponential-backoff retry."""
        if self._client is not None:
            return

        delay = _RETRY_DELAY
        last_error: Exception = RuntimeError("No connection attempt made")

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                self._client = MongoClient(
                    MONGO_URI,
                    serverSelectionTimeoutMS=8000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=10000,
                    retryWrites=True,
                    maxPoolSize=10,
                    minPoolSize=1,
                )
                self._client.admin.command("ping")
                self._db = self._client[MONGO_DB_NAME]
                logger.info("Connected to MongoDB: %s (attempt %d)", MONGO_DB_NAME, attempt)
                return
            except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
                last_error = exc
                logger.warning(
                    "MongoDB connection attempt %d/%d failed: %s",
                    attempt, _MAX_RETRIES, exc,
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(delay)
                    delay *= 2
            except Exception as exc:
                last_error = exc
                logger.error("Unexpected MongoDB error on attempt %d: %s", attempt, exc)
                break

        self._client = None
        self._db = None
        raise ConnectionError(
            f"Could not connect to MongoDB after {_MAX_RETRIES} attempts: {last_error}"
        ) from last_error

    @property
    def db(self) -> Optional[Database]:
        """Get the database instance, connecting if necessary."""
        if self._db is None:
            self.connect()
        return self._db

    def get_collection(self, name: str) -> Collection:
        """Get a collection by name."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db[name]

    def is_alive(self) -> bool:
        """Check whether the MongoDB connection is healthy."""
        try:
            if self._client is None:
                return False
            self._client.admin.command("ping")
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")


# ── Module-level singleton ────────────────────────────────────────────────────

_connection: Optional[MongoDBConnection] = None


def get_connection() -> MongoDBConnection:
    """Return the global MongoDB connection singleton, connecting on first call."""
    global _connection
    if _connection is None:
        _connection = MongoDBConnection()
        _connection.connect()
    return _connection


def get_db() -> Database:
    """Return the database instance directly."""
    return get_connection().db
