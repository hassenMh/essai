from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from app.views.widgets.stat_card import StatCard
from app.controllers.sale_controller import SaleController
from app.controllers.product_controller import ProductController
from app.controllers.stock_controller import StockController
from app.controllers.expense_controller import ExpenseController
from app.utils.helpers import format_price, today_str, first_day_of_month


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(24)

        # Top greeting
        greet_row = QHBoxLayout()
        self._greeting = QLabel("Tableau de bord")
        self._greeting.setStyleSheet("font-size: 24px; font-weight: 700;")
        self._date_lbl = QLabel()
        self._date_lbl.setStyleSheet("color: #9AA0C4; font-size: 13px;")
        self._date_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        greet_row.addWidget(self._greeting)
        greet_row.addWidget(self._date_lbl, 1)

        refresh_btn = QPushButton("↻  Actualiser")
        refresh_btn.setObjectName("btnSecondary")
        refresh_btn.setFixedWidth(130)
        refresh_btn.clicked.connect(self.refresh)
        greet_row.addWidget(refresh_btn)
        main.addLayout(greet_row)

        # KPI Cards row
        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        self._card_revenue  = StatCard("Chiffre d'affaires (Aujourd'hui)", "0.000 TND", "💰", "#7B8CDE")
        self._card_sales    = StatCard("Ventes (Aujourd'hui)", "0", "🧾", "#43A047")
        self._card_products = StatCard("Produits actifs", "0", "📦", "#FB8C00")
        self._card_low      = StatCard("Stock faible", "0", "⚠️", "#E53935")

        cards_grid.addWidget(self._card_revenue,  0, 0)
        cards_grid.addWidget(self._card_sales,    0, 1)
        cards_grid.addWidget(self._card_products, 0, 2)
        cards_grid.addWidget(self._card_low,      0, 3)
        main.addLayout(cards_grid)

        # Monthly KPIs
        month_row = QHBoxLayout()
        month_row.setSpacing(16)
        self._card_month    = StatCard("CA du mois", "0.000 TND", "📈", "#00BCD4")
        self._card_inv_val  = StatCard("Valeur du stock", "0.000 TND", "🏭", "#9C27B0")
        self._card_expenses = StatCard("Dépenses du mois", "0.000 TND", "💸", "#FF5722")
        month_row.addWidget(self._card_month)
        month_row.addWidget(self._card_inv_val)
        month_row.addWidget(self._card_expenses)
        main.addLayout(month_row)

        # Bottom row: low stock + top products
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Low stock panel
        low_stock_frame = QFrame()
        low_stock_frame.setObjectName("statCard")
        ls_layout = QVBoxLayout(low_stock_frame)
        ls_layout.setContentsMargins(16, 16, 16, 16)

        ls_title = QLabel("⚠️  Produits en stock faible")
        ls_title.setStyleSheet("font-weight: 700; font-size: 15px;")
        ls_layout.addWidget(ls_title)

        self._low_stock_scroll = QScrollArea()
        self._low_stock_scroll.setWidgetResizable(True)
        self._low_stock_scroll.setFrameShape(QFrame.NoFrame)
        self._low_stock_inner = QWidget()
        self._low_stock_layout = QVBoxLayout(self._low_stock_inner)
        self._low_stock_layout.setSpacing(4)
        self._low_stock_scroll.setWidget(self._low_stock_inner)
        ls_layout.addWidget(self._low_stock_scroll)

        # Top products panel
        top_frame = QFrame()
        top_frame.setObjectName("statCard")
        tp_layout = QVBoxLayout(top_frame)
        tp_layout.setContentsMargins(16, 16, 16, 16)

        tp_title = QLabel("🏆  Top produits (ce mois)")
        tp_title.setStyleSheet("font-weight: 700; font-size: 15px;")
        tp_layout.addWidget(tp_title)

        self._top_scroll = QScrollArea()
        self._top_scroll.setWidgetResizable(True)
        self._top_scroll.setFrameShape(QFrame.NoFrame)
        self._top_inner = QWidget()
        self._top_layout = QVBoxLayout(self._top_inner)
        self._top_layout.setSpacing(4)
        self._top_scroll.setWidget(self._top_inner)
        tp_layout.addWidget(self._top_scroll)

        bottom_row.addWidget(low_stock_frame, 1)
        bottom_row.addWidget(top_frame, 1)
        main.addLayout(bottom_row, 1)

    def refresh(self):
        from datetime import datetime
        now = datetime.now()
        self._date_lbl.setText(now.strftime("%A %d %B %Y  %H:%M"))

        today = today_str()
        month_start = first_day_of_month()

        daily = SaleController.get_daily_summary()
        self._card_revenue.set_value(format_price(daily.get("revenue", 0)))
        self._card_sales.set_value(str(daily.get("total_sales", 0)))

        inv = StockController.get_inventory_value()
        self._card_products.set_value(str(inv.get("product_count", 0)))
        self._card_low.set_value(str(inv.get("low_stock_count", 0)))
        self._card_inv_val.set_value(format_price(inv.get("sale_value", 0)))

        monthly_sales = SaleController.get_daily_summary.__func__ if False else None
        from app.database.connection import db
        month_rev = db.fetchone(
            "SELECT COALESCE(SUM(total),0) AS r FROM sales WHERE date(created_at)>=? AND status='completed'",
            (month_start,)
        )
        self._card_month.set_value(format_price(month_rev.get("r", 0) if month_rev else 0))

        month_exp = ExpenseController.get_summary(date_from=month_start)
        self._card_expenses.set_value(format_price(month_exp.get("total", 0)))

        # Low stock list
        self._clear_layout(self._low_stock_layout)
        low = ProductController.get_low_stock()
        if not low:
            lbl = QLabel("Aucun produit en stock faible ✓")
            lbl.setStyleSheet("color: #43A047; padding: 8px;")
            self._low_stock_layout.addWidget(lbl)
        for p in low[:10]:
            row = self._make_stock_row(p)
            self._low_stock_layout.addWidget(row)
        self._low_stock_layout.addStretch()

        # Top products
        self._clear_layout(self._top_layout)
        top = SaleController.get_top_products(10, date_from=month_start)
        for i, p in enumerate(top):
            row = self._make_top_row(i + 1, p)
            self._top_layout.addWidget(row)
        if not top:
            lbl = QLabel("Aucune vente ce mois.")
            lbl.setStyleSheet("color: #9AA0C4; padding: 8px;")
            self._top_layout.addWidget(lbl)
        self._top_layout.addStretch()

    def _make_stock_row(self, product: dict) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background: #252848; border-radius: 8px; padding: 4px 0;")
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)

        name = QLabel(product["name"])
        name.setStyleSheet("font-weight: 600;")

        qty_text = f"{product['stock_quantity']:.1f} / {product['min_stock']:.1f}"
        qty = QLabel(qty_text)
        qty.setObjectName("badge")
        qty.setAlignment(Qt.AlignCenter)

        row.addWidget(name, 1)
        row.addWidget(qty)
        return frame

    def _make_top_row(self, rank: int, product: dict) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background: #252848; border-radius: 8px;")
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)

        rank_lbl = QLabel(f"#{rank}")
        rank_lbl.setStyleSheet("color: #9AA0C4; font-weight: 700; min-width: 28px;")

        name = QLabel(product["name"])
        name.setStyleSheet("font-weight: 600;")

        rev = QLabel(format_price(product.get("total_revenue", 0)))
        rev.setObjectName("badgeSuccess")
        rev.setAlignment(Qt.AlignCenter)

        row.addWidget(rank_lbl)
        row.addWidget(name, 1)
        row.addWidget(rev)
        return frame

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
