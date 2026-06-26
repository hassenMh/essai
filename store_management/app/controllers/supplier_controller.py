from app.database.connection import db
from app.controllers.auth_controller import AuthController


class SupplierController:

    @staticmethod
    def get_all() -> list[dict]:
        return db.fetchall("SELECT * FROM suppliers ORDER BY name")

    @staticmethod
    def get_by_id(sup_id: int) -> dict | None:
        return db.fetchone("SELECT * FROM suppliers WHERE id=?", (sup_id,))

    @staticmethod
    def create(data: dict) -> int:
        cur = db.execute(
            "INSERT INTO suppliers (name, phone, email, address, notes) VALUES (?,?,?,?,?)",
            (data["name"], data.get("phone"), data.get("email"), data.get("address"), data.get("notes")),
        )
        AuthController.log("SUPPLIER_CREATE", f"Fournisseur créé: {data['name']}")
        return cur.lastrowid

    @staticmethod
    def update(sup_id: int, data: dict):
        db.execute(
            "UPDATE suppliers SET name=?, phone=?, email=?, address=?, notes=? WHERE id=?",
            (data["name"], data.get("phone"), data.get("email"), data.get("address"), data.get("notes"), sup_id),
        )
        AuthController.log("SUPPLIER_UPDATE", f"Fournisseur modifié: id={sup_id}")

    @staticmethod
    def delete(sup_id: int):
        db.execute("DELETE FROM suppliers WHERE id=?", (sup_id,))
        AuthController.log("SUPPLIER_DELETE", f"Fournisseur supprimé: id={sup_id}")
