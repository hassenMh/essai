from app.database.connection import db
from app.controllers.auth_controller import AuthController
from app.controllers.product_controller import ProductController


class SaleController:

    @staticmethod
    def create_sale(items: list[dict], payment_method: str = "cash",
                    discount: float = 0, tax_rate: float = 0,
                    amount_paid: float = 0, notes: str = "") -> dict:
        """
        items: [{"product_id": int, "quantity": float, "unit_price": float, "discount": float}]
        Returns the created sale dict including the receipt info.
        """
        subtotal = sum(it["quantity"] * it["unit_price"] - it.get("discount", 0) for it in items)
        tax = round(subtotal * tax_rate / 100, 3)
        total = round(subtotal - discount + tax, 3)
        change = round(amount_paid - total, 3)

        user_id = AuthController.current_user()["id"]
        cur = db.execute("""
            INSERT INTO sales (user_id, subtotal, discount, tax, total, payment_method, amount_paid, change_given, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (user_id, subtotal, discount, tax, total, payment_method, amount_paid, change, notes))
        sale_id = cur.lastrowid

        for it in items:
            item_total = round(it["quantity"] * it["unit_price"] - it.get("discount", 0), 3)
            db.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount, total)
                VALUES (?,?,?,?,?,?)
            """, (sale_id, it["product_id"], it["quantity"], it["unit_price"], it.get("discount", 0), item_total))
            ProductController.update_stock(
                it["product_id"], -it["quantity"], "out", f"Vente #{sale_id}"
            )

        AuthController.log("SALE_CREATE", f"Vente #{sale_id} | Total: {total}")
        return SaleController.get_by_id(sale_id)

    @staticmethod
    def get_by_id(sale_id: int) -> dict | None:
        sale = db.fetchone("""
            SELECT s.*, u.full_name AS cashier_name
            FROM sales s JOIN users u ON u.id=s.user_id
            WHERE s.id=?
        """, (sale_id,))
        if sale:
            sale["items"] = db.fetchall("""
                SELECT si.*, p.name AS product_name, p.unit_type
                FROM sale_items si JOIN products p ON p.id=si.product_id
                WHERE si.sale_id=?
            """, (sale_id,))
        return sale

    @staticmethod
    def get_sales(date_from: str = None, date_to: str = None,
                  user_id: int = None, status: str = None) -> list[dict]:
        conds = []
        params = []
        if date_from:
            conds.append("date(s.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conds.append("date(s.created_at) <= date(?)")
            params.append(date_to)
        if user_id:
            conds.append("s.user_id=?")
            params.append(user_id)
        if status:
            conds.append("s.status=?")
            params.append(status)
        where = "WHERE " + " AND ".join(conds) if conds else ""
        return db.fetchall(f"""
            SELECT s.*, u.full_name AS cashier_name,
                   (SELECT COUNT(*) FROM sale_items WHERE sale_id=s.id) AS item_count
            FROM sales s JOIN users u ON u.id=s.user_id
            {where}
            ORDER BY s.created_at DESC
        """, tuple(params))

    @staticmethod
    def cancel_sale(sale_id: int, reason: str = ""):
        sale = SaleController.get_by_id(sale_id)
        if not sale or sale["status"] != "completed":
            raise ValueError("Vente introuvable ou déjà annulée.")
        db.execute("UPDATE sales SET status='cancelled' WHERE id=?", (sale_id,))
        for item in sale["items"]:
            ProductController.update_stock(
                item["product_id"], item["quantity"], "return", f"Annulation vente #{sale_id}"
            )
        AuthController.log("SALE_CANCEL", f"Vente #{sale_id} annulée. Raison: {reason}")

    @staticmethod
    def get_daily_summary(date: str = None) -> dict:
        d = date or "date('now','localtime')"
        p = (date,) if date else ()
        cond = "date(created_at)=?" if date else "date(created_at)=date('now','localtime')"
        row = db.fetchone(f"""
            SELECT
                COUNT(*) AS total_sales,
                COALESCE(SUM(total), 0) AS revenue,
                COALESCE(SUM(discount), 0) AS total_discounts,
                COALESCE(SUM(tax), 0) AS total_taxes
            FROM sales WHERE {cond} AND status='completed'
        """, p)
        return row or {}

    @staticmethod
    def get_top_products(limit: int = 10, date_from: str = None, date_to: str = None) -> list[dict]:
        conds = ["s.status='completed'"]
        params = []
        if date_from:
            conds.append("date(s.created_at)>=?")
            params.append(date_from)
        if date_to:
            conds.append("date(s.created_at)<=?")
            params.append(date_to)
        where = "WHERE " + " AND ".join(conds)
        return db.fetchall(f"""
            SELECT p.name, p.unit_type,
                   SUM(si.quantity) AS total_qty,
                   SUM(si.total) AS total_revenue
            FROM sale_items si
            JOIN sales s ON s.id=si.sale_id
            JOIN products p ON p.id=si.product_id
            {where}
            GROUP BY si.product_id
            ORDER BY total_revenue DESC
            LIMIT {limit}
        """, tuple(params))

    @staticmethod
    def get_revenue_by_period(period: str = "day", days: int = 30) -> list[dict]:
        fmt_map = {"day": "%d/%m", "week": "Sem %W", "month": "%m/%Y"}
        fmt = fmt_map.get(period, "%d/%m")
        return db.fetchall(f"""
            SELECT strftime('{fmt}', created_at) AS period,
                   SUM(total) AS revenue,
                   COUNT(*) AS sales_count
            FROM sales
            WHERE status='completed'
              AND date(created_at) >= date('now','localtime','-{days} days')
            GROUP BY period
            ORDER BY created_at
        """)
