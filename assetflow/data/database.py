"""SQLite persistence for the AssetFlow domain registry.

The application keeps its existing object-based workflow, while this module
stores the complete registry atomically in a local SQLite database after every
business event.  This makes new assets and their availability survive dashboard
restarts without changing the existing allocation or maintenance contracts.
"""

from __future__ import annotations

import pickle
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("assetflow.db")


class SQLiteStateStore:
    def __init__(self, database_path: Path = DATABASE_PATH):
        self.database_path = database_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS assetflow_state (
                    state_key TEXT PRIMARY KEY,
                    payload BLOB NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save(self, registry) -> None:
        payload = sqlite3.Binary(pickle.dumps(registry, protocol=pickle.HIGHEST_PROTOCOL))
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO assetflow_state (state_key, payload, updated_at)
                VALUES ('registry', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(state_key) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (payload,),
            )

    def load(self):
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT payload FROM assetflow_state WHERE state_key = 'registry'"
            ).fetchone()
        return pickle.loads(row[0]) if row else None

