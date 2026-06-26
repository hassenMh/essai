from __future__ import annotations
import bcrypt
from app.database.connection import db


class AuthController:
    _current_user: dict | None = None

    @classmethod
    def login(cls, username: str, password: str) -> dict | None:
        user = db.fetchone(
            "SELECT * FROM users WHERE username=? AND is_active=1",
            (username,),
        )
        if not user:
            return None
        if bcrypt.checkpw(password.encode(), user["password"].encode()):
            cls._current_user = user
            cls._log_action("LOGIN", f"Connexion réussie")
            return user
        return None

    @classmethod
    def logout(cls):
        if cls._current_user:
            cls._log_action("LOGOUT", "Déconnexion")
        cls._current_user = None

    @classmethod
    def current_user(cls) -> dict | None:
        return cls._current_user

    @classmethod
    def is_admin(cls) -> bool:
        return cls._current_user is not None and cls._current_user["role"] == "admin"

    @classmethod
    def _log_action(cls, action: str, details: str = ""):
        if cls._current_user:
            db.execute(
                "INSERT INTO user_logs (user_id, action, details) VALUES (?,?,?)",
                (cls._current_user["id"], action, details),
            )

    @classmethod
    def log(cls, action: str, details: str = ""):
        cls._log_action(action, details)
