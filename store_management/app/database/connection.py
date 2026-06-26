from __future__ import annotations
import sqlite3
import threading
from pathlib import Path
from config import DATABASE_PATH, ensure_dirs


class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        ensure_dirs()
        self._db_path = str(DATABASE_PATH)
        self._local = threading.local()
        self._initialized = True

    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor

    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        conn = self.get_connection()
        cursor = conn.executemany(query, params_list)
        conn.commit()
        return cursor

    def fetchall(self, query: str, params: tuple = ()) -> list:
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def fetchone(self, query: str, params: tuple = ()) -> dict | None:
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None


db = DatabaseConnection()
