from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QFormLayout, QDoubleSpinBox, QLineEdit, QComboBox,
    QMessageBox, QFrame,
)
from PySide6.QtCore import Qt

from app.views.widgets.data_table import DataTable
from app.views.widgets.search_bar import SearchBar
from app.controllers.stock_controller import StockController
from app.controllers.product_controller import ProductController
from app.utils.helpers import format_datetime


class StockView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Inventory value banner
        self._inv_frame = QFrame()
        self._inv_frame.setObjectName("statCard")
        inv_row = QHBoxLayout(self._inv_frame)
        self._lbl_purchase = QLabel()
        self._lbl_sale = QLabel()
        self._lbl_count = QLabel()
        for lbl in [self._lbl_purchase, self._lbl_sale, self._lbl_count]:
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 14px;")
            inv_row.addWidget(lbl, 1)
        layout.addWidget(self._inv_frame)

        # Toolbar
        toolbar = QHBoxLayout()
        self._search = SearchBar("🔍  Rechercher un produit...")
        self._search.setMinimumHeight(42)
        self._search.search_changed.connect(self._filter_movements)

        btn_adjust = QPushButton("📋  Ajustement stock")
        btn_adjust.setObjectName("btnWarning")
        btn_adjust.setMinimumHeight(42)
        btn_adjust.clicked.connect(self._open_adjust)

        btn_entry = QPushButton("📦  Entrée stock")
        btn_entry.setObjectName("btnSuccess")
        btn_entry.setMinimumHeight(42)
        btn_entry.clicked.connect(self._open_entry)

        toolbar.addWidget(self._search, 1)
        toolbar.addWidget(btn_adjust)
        toolbar.addWidget(btn_entry)
        layout.addLayout(toolbar)

        # Movements table
        lbl = QLabel("Historique des mouvements de stock")
        lbl.setStyleSheet("font-size: 15px; font-weight: 600;")
        layout.addWidget(lbl)

        self._table = DataTable(["Date", "Produit", "Type", "Quantité", "Référence", "Notes", "Utilisateur"])
        layout.addWidget(self._table, 1)

    def refresh(self):
        inv = StockController.get_inventory_value()
        from app.utils.helpers import format_price
        self._lbl_purchase.setText(f"<b>Valeur achat</b><br>{format_price(inv.get('purchase_value', 0))}")
        self._lbl_sale.setText(f"<b>Valeur vente</b><br>{format_price(inv.get('sale_value', 0))}")
        self._lbl_count.setText(f"<b>Produits</b><br>{inv.get('product_count', 0)} ({inv.get('low_stock_count', 0)} en stock faible)")
        self._load_movements()

    def _load_movements(self, product_id: int = None):
        movements = StockController.get_movements(product_id)
        type_labels = {"in": "✅ Entrée", "out": "📤 Sortie", "adjustment": "⚙️ Ajustement", "return": "↩️ Retour"}
        display = []
        for m in movements:
            d = dict(m)
            d["created_at"] = format_datetime(m["created_at"])
            d["movement_type"] = type_labels.get(m["movement_type"], m["movement_type"])
            d["quantity"] = f"{m['quantity']:.2f}"
            display.append(d)
        self._table.set_data(display, ["created_at", "product_name", "movement_type", "quantity", "reference", "notes", "user_name"])

    def _filter_movements(self, text: str):
        if not text:
            self._load_movements()
            return
        products = ProductController.search(text)
        if products:
            self._load_movements(products[0]["id"])

    def _open_adjust(self):
        dlg = StockAdjustDialog(self)
        if dlg.exec():
            self.refresh()

    def _open_entry(self):
        dlg = StockEntryDialog(self)
        if dlg.exec():
            self.refresh()


class StockAdjustDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajustement de stock")
        self.setFixedWidth(420)
        self._products = ProductController.get_all()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(QLabel("<b>Ajustement d'inventaire</b>"))

        form = QFormLayout()
        self._product_combo = QComboBox()
        self._product_combo.setMinimumHeight(42)
        for p in self._products:
            self._product_combo.addItem(f"{p['name']} (stock: {p['stock_quantity']:.2f})", p["id"])
        self._product_combo.currentIndexChanged.connect(self._update_current)

        self._current_lbl = QLabel()
        self._new_qty = QDoubleSpinBox()
        self._new_qty.setMinimumHeight(42)
        self._new_qty.setMaximum(999999)
        self._new_qty.setDecimals(2)

        self._notes = QLineEdit()
        self._notes.setMinimumHeight(42)
        self._notes.setPlaceholderText("Raison de l'ajustement...")

        form.addRow("Produit:", self._product_combo)
        form.addRow("Stock actuel:", self._current_lbl)
        form.addRow("Nouveau stock:", self._new_qty)
        form.addRow("Notes:", self._notes)
        layout.addLayout(form)
        self._update_current()

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("✅  Confirmer")
        btn_ok.clicked.connect(self._confirm)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _update_current(self):
        pid = self._product_combo.currentData()
        p = next((x for x in self._products if x["id"] == pid), None)
        if p:
            self._current_lbl.setText(f"{p['stock_quantity']:.2f} {p['unit_type']}")
            self._new_qty.setValue(p["stock_quantity"])

    def _confirm(self):
        pid = self._product_combo.currentData()
        StockController.adjust_stock(pid, self._new_qty.value(), self._notes.text() or "Ajustement inventaire")
        self.accept()


class StockEntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Entrée de stock")
        self.setFixedWidth(420)
        self._products = ProductController.get_all()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        self._product_combo = QComboBox()
        self._product_combo.setMinimumHeight(42)
        for p in self._products:
            self._product_combo.addItem(p["name"], p["id"])

        self._qty = QDoubleSpinBox()
        self._qty.setMinimumHeight(42)
        self._qty.setMinimum(0.01)
        self._qty.setMaximum(99999)
        self._qty.setDecimals(2)
        self._qty.setValue(1)

        self._ref = QLineEdit()
        self._ref.setMinimumHeight(42)
        self._ref.setPlaceholderText("N° BL, fournisseur...")

        self._notes = QLineEdit()
        self._notes.setMinimumHeight(42)

        form.addRow("Produit:", self._product_combo)
        form.addRow("Quantité:", self._qty)
        form.addRow("Référence:", self._ref)
        form.addRow("Notes:", self._notes)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("✅  Confirmer")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.clicked.connect(self._confirm)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _confirm(self):
        pid = self._product_combo.currentData()
        StockController.add_stock(pid, self._qty.value(), self._notes.text(), self._ref.text())
        self.accept()
