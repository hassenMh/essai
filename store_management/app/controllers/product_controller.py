from app.database.connection import db
from app.controllers.auth_controller import AuthController


class ProductController:

    @staticmethod
    def get_all(include_inactive: bool = False) -> list[dict]:
        where = "" if include_inactive else "WHERE p.is_active=1"
        return db.fetchall(f"""
            SELECT p.*, c.name AS category_name, s.name AS supplier_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN suppliers  s ON s.id = p.supplier_id
            {where}
            ORDER BY p.name
        """)

    @staticmethod
    def get_by_id(product_id: int) -> dict | None:
        return db.fetchone("""
            SELECT p.*, c.name AS category_name, s.name AS supplier_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN suppliers  s ON s.id = p.supplier_id
            WHERE p.id=?
        """, (product_id,))

    @staticmethod
    def get_by_barcode(barcode: str) -> dict | None:
        return db.fetchone("""
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.barcode=? AND p.is_active=1
        """, (barcode,))

    @staticmethod
    def search(query: str) -> list[dict]:
        q = f"%{query}%"
        return db.fetchall("""
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.is_active=1 AND (p.name LIKE ? OR p.barcode LIKE ? OR c.name LIKE ?)
            ORDER BY p.name
        """, (q, q, q))

    @staticmethod
    def create(data: dict) -> int:
        cur = db.execute("""
            INSERT INTO products
                (barcode, name, category_id, supplier_id, purchase_price, sale_price,
                 stock_quantity, min_stock, unit_type, expiry_date, description, image_path)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("barcode"), data["name"], data.get("category_id"),
            data.get("supplier_id"), data.get("purchase_price", 0),
            data["sale_price"], data.get("stock_quantity", 0),
            data.get("min_stock", 5), data.get("unit_type", "piece"),
            data.get("expiry_date"), data.get("description"), data.get("image_path"),
        ))
        product_id = cur.lastrowid
        AuthController.log("PRODUCT_CREATE", f"Produit créé: {data['name']} (id={product_id})")
        if data.get("stock_quantity", 0) > 0:
            db.execute("""
                INSERT INTO stock_movements (product_id, user_id, movement_type, quantity, notes)
                VALUES (?,?,?,?,?)
            """, (product_id, AuthController.current_user()["id"], "in", data["stock_quantity"], "Stock initial"))
        return product_id

    @staticmethod
    def update(product_id: int, data: dict):
        db.execute("""
            UPDATE products SET
                barcode=?, name=?, category_id=?, supplier_id=?,
                purchase_price=?, sale_price=?, min_stock=?, unit_type=?,
                expiry_date=?, description=?, image_path=?,
                updated_at=datetime('now','localtime')
            WHERE id=?
        """, (
            data.get("barcode"), data["name"], data.get("category_id"),
            data.get("supplier_id"), data.get("purchase_price", 0),
            data["sale_price"], data.get("min_stock", 5),
            data.get("unit_type", "piece"), data.get("expiry_date"),
            data.get("description"), data.get("image_path"), product_id,
        ))
        AuthController.log("PRODUCT_UPDATE", f"Produit modifié: id={product_id}")

    @staticmethod
    def delete(product_id: int):
        db.execute("UPDATE products SET is_active=0 WHERE id=?", (product_id,))
        AuthController.log("PRODUCT_DELETE", f"Produit supprimé: id={product_id}")

    @staticmethod
    def update_stock(product_id: int, quantity_delta: float, movement_type: str, notes: str = ""):
        db.execute(
            "UPDATE products SET stock_quantity=stock_quantity+?, updated_at=datetime('now','localtime') WHERE id=?",
            (quantity_delta, product_id),
        )
        user_id = AuthController.current_user()["id"]
        db.execute("""
            INSERT INTO stock_movements (product_id, user_id, movement_type, quantity, notes)
            VALUES (?,?,?,?,?)
        """, (product_id, user_id, movement_type, abs(quantity_delta), notes))

    @staticmethod
    def get_low_stock() -> list[dict]:
        return db.fetchall("""
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id=p.category_id
            WHERE p.is_active=1 AND p.stock_quantity <= p.min_stock
            ORDER BY p.stock_quantity
        """)

    @staticmethod
    def get_expiring_soon(days: int = 7) -> list[dict]:
        return db.fetchall(f"""
            SELECT * FROM products
            WHERE is_active=1 AND expiry_date IS NOT NULL
              AND date(expiry_date) <= date('now','localtime','+{days} days')
            ORDER BY expiry_date
        """)
