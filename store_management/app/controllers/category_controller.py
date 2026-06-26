from app.database.connection import db
from app.controllers.auth_controller import AuthController


class CategoryController:

    @staticmethod
    def get_all() -> list[dict]:
        return db.fetchall("SELECT * FROM categories ORDER BY name")

    @staticmethod
    def get_by_id(cat_id: int) -> dict | None:
        return db.fetchone("SELECT * FROM categories WHERE id=?", (cat_id,))

    @staticmethod
    def create(name: str, description: str = "", color: str = "#4CAF50") -> int:
        cur = db.execute(
            "INSERT INTO categories (name, description, color) VALUES (?,?,?)",
            (name, description, color),
        )
        AuthController.log("CATEGORY_CREATE", f"Catégorie créée: {name}")
        return cur.lastrowid

    @staticmethod
    def update(cat_id: int, name: str, description: str = "", color: str = "#4CAF50"):
        db.execute(
            "UPDATE categories SET name=?, description=?, color=? WHERE id=?",
            (name, description, color, cat_id),
        )
        AuthController.log("CATEGORY_UPDATE", f"Catégorie modifiée: id={cat_id}")

    @staticmethod
    def delete(cat_id: int):
        count = db.fetchone("SELECT COUNT(*) as c FROM products WHERE category_id=?", (cat_id,))
        if count and count["c"] > 0:
            raise ValueError("Cette catégorie contient des produits.")
        db.execute("DELETE FROM categories WHERE id=?", (cat_id,))
        AuthController.log("CATEGORY_DELETE", f"Catégorie supprimée: id={cat_id}")
