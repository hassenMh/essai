from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QMessageBox, QDialog,
    QFormLayout, QDoubleSpinBox, QComboBox, QSpinBox, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent

from app.controllers.product_controller import ProductController
from app.controllers.sale_controller import SaleController
from app.controllers.auth_controller import AuthController
from app.database.connection import db
from app.utils.helpers import format_price
from app.utils.exporter import generate_receipt_pdf
import subprocess, sys


class POSView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cart: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left: Search + products ──────────────────────────
        left = QWidget()
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(24, 24, 16, 24)
        left_layout.setSpacing(16)

        # Search bar
        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  Scanner QR / Saisir nom ou code-barres...")
        self._search_input.setMinimumHeight(52)
        self._search_input.setObjectName("searchBar")
        self._search_input.returnPressed.connect(self._on_scan)
        self._search_input.textChanged.connect(self._live_search)

        btn_scan = QPushButton("⊞ Scanner")
        btn_scan.setMinimumHeight(52)
        btn_scan.clicked.connect(self._on_scan)
        search_row.addWidget(self._search_input, 1)
        search_row.addWidget(btn_scan)
        left_layout.addLayout(search_row)

        # Product grid (results)
        self._result_label = QLabel("Résultats de recherche")
        self._result_label.setStyleSheet("font-size: 13px; color: #9AA0C4;")
        left_layout.addWidget(self._result_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._grid_widget = QWidget()
        self._grid_layout = QVBoxLayout(self._grid_widget)
        self._grid_layout.setSpacing(8)
        self._grid_layout.addStretch()
        scroll.setWidget(self._grid_widget)
        left_layout.addWidget(scroll, 1)

        root.addWidget(left, 1)

        # ── Right: Cart ──────────────────────────────────────
        cart_panel = QFrame()
        cart_panel.setObjectName("cartPanel")
        cart_layout = QVBoxLayout(cart_panel)
        cart_layout.setContentsMargins(0, 0, 0, 0)
        cart_layout.setSpacing(0)

        cart_header = QFrame()
        cart_header.setStyleSheet("background: #12141F; border-bottom: 1px solid #2D3055;")
        ch_layout = QHBoxLayout(cart_header)
        ch_layout.setContentsMargins(16, 14, 16, 14)
        cart_title = QLabel("🛒  Panier")
        cart_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        btn_clear = QPushButton("Vider")
        btn_clear.setObjectName("btnDanger")
        btn_clear.setFixedHeight(34)
        btn_clear.clicked.connect(self._clear_cart)
        ch_layout.addWidget(cart_title, 1)
        ch_layout.addWidget(btn_clear)
        cart_layout.addWidget(cart_header)

        # Cart items list
        cart_scroll = QScrollArea()
        cart_scroll.setWidgetResizable(True)
        cart_scroll.setFrameShape(QFrame.NoFrame)
        self._cart_widget = QWidget()
        self._cart_layout = QVBoxLayout(self._cart_widget)
        self._cart_layout.setContentsMargins(8, 8, 8, 8)
        self._cart_layout.setSpacing(6)
        self._cart_layout.addStretch()
        cart_scroll.setWidget(self._cart_widget)
        cart_layout.addWidget(cart_scroll, 1)

        # Total
        total_frame = QFrame()
        total_frame.setObjectName("cartTotal")
        total_frame.setStyleSheet("background: #7B8CDE; border-radius: 12px; margin: 8px;")
        tf_layout = QVBoxLayout(total_frame)

        self._subtotal_lbl = QLabel("Sous-total : 0.000 TND")
        self._subtotal_lbl.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 12px; background: transparent;")
        self._discount_lbl = QLabel("")
        self._discount_lbl.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 12px; background: transparent;")
        self._total_lbl = QLabel("TOTAL : 0.000 TND")
        self._total_lbl.setObjectName("cartTotalLabel")
        self._total_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: white; background: transparent;")

        tf_layout.addWidget(self._subtotal_lbl)
        tf_layout.addWidget(self._discount_lbl)
        tf_layout.addWidget(self._total_lbl)
        cart_layout.addWidget(total_frame)

        # Discount row
        disc_row = QHBoxLayout()
        disc_row.setContentsMargins(8, 0, 8, 4)
        disc_lbl = QLabel("Remise :")
        disc_lbl.setStyleSheet("color: #9AA0C4; font-size: 12px;")
        self._discount_spin = QDoubleSpinBox()
        self._discount_spin.setMaximum(99999)
        self._discount_spin.setDecimals(3)
        self._discount_spin.setSuffix(" TND")
        self._discount_spin.setMaximumHeight(36)
        self._discount_spin.valueChanged.connect(self._update_totals)
        disc_row.addWidget(disc_lbl)
        disc_row.addWidget(self._discount_spin, 1)
        cart_layout.addLayout(disc_row)

        # Payment buttons
        pay_layout = QVBoxLayout()
        pay_layout.setContentsMargins(8, 4, 8, 8)
        pay_layout.setSpacing(8)

        btn_pay_cash = QPushButton("💵  Payer en espèces")
        btn_pay_cash.setMinimumHeight(52)
        btn_pay_cash.setStyleSheet("font-size: 15px; font-weight: 700; background: #43A047;")
        btn_pay_cash.clicked.connect(lambda: self._checkout("cash"))

        btn_pay_card = QPushButton("💳  Payer par carte")
        btn_pay_card.setMinimumHeight(44)
        btn_pay_card.setObjectName("btnSecondary")
        btn_pay_card.clicked.connect(lambda: self._checkout("card"))

        pay_layout.addWidget(btn_pay_cash)
        pay_layout.addWidget(btn_pay_card)
        cart_layout.addLayout(pay_layout)

        root.addWidget(cart_panel)

    # ── Search / Scan ─────────────────────────────────────────

    def _on_scan(self):
        code = self._search_input.text().strip()
        if not code:
            return
        product = ProductController.get_by_barcode(code)
        if product:
            if product["unit_type"] in ("kg", "litre"):
                self._ask_weight(product)
            else:
                self._add_to_cart(product, 1)
            self._search_input.clear()
        else:
            self._live_search(code)

    def _live_search(self, text: str):
        if len(text) < 2:
            self._clear_results()
            return
        products = ProductController.search(text)
        self._display_results(products)

    def _display_results(self, products: list):
        self._clear_results()
        if not products:
            lbl = QLabel("Aucun produit trouvé")
            lbl.setStyleSheet("color: #9AA0C4; padding: 20px;")
            lbl.setAlignment(Qt.AlignCenter)
            self._grid_layout.insertWidget(0, lbl)
            return
        self._result_label.setText(f"{len(products)} produit(s) trouvé(s)")
        for p in products[:20]:
            card = self._make_product_card(p)
            self._grid_layout.insertWidget(self._grid_layout.count() - 1, card)

    def _make_product_card(self, product: dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: #1E2235; border: 1px solid #2D3055; border-radius: 10px; }
            QFrame:hover { border-color: #7B8CDE; background: #252848; }
        """)
        card.setCursor(Qt.PointingHandCursor)
        row = QHBoxLayout(card)
        row.setContentsMargins(14, 12, 14, 12)

        info = QVBoxLayout()
        name = QLabel(product["name"])
        name.setStyleSheet("font-weight: 600; font-size: 14px;")
        cat = QLabel(product.get("category_name") or "—")
        cat.setStyleSheet("color: #9AA0C4; font-size: 12px;")
        info.addWidget(name)
        info.addWidget(cat)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        price = QLabel(format_price(product["sale_price"]))
        price.setStyleSheet("font-weight: 700; color: #7B8CDE; font-size: 15px;")
        stock = QLabel(f"Stock: {product['stock_quantity']:.1f}")
        stock.setStyleSheet("color: #9AA0C4; font-size: 11px;")
        right.addWidget(price)
        right.addWidget(stock)

        row.addLayout(info, 1)
        row.addLayout(right)

        # Click = add to cart
        def on_click(event, p=product):
            if p["unit_type"] in ("kg", "litre"):
                self._ask_weight(p)
            else:
                self._add_to_cart(p, 1)
            self._search_input.clear()
            self._clear_results()

        card.mousePressEvent = on_click
        return card

    def _clear_results(self):
        while self._grid_layout.count() > 1:
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._result_label.setText("Résultats de recherche")

    # ── Cart management ───────────────────────────────────────

    def _add_to_cart(self, product: dict, quantity: float):
        for item in self._cart:
            if item["product_id"] == product["id"]:
                if product["stock_quantity"] < item["quantity"] + quantity:
                    QMessageBox.warning(self, "Stock insuffisant",
                                        f"Stock disponible : {product['stock_quantity']:.2f}")
                    return
                item["quantity"] += quantity
                self._render_cart()
                return

        if product["stock_quantity"] < quantity:
            QMessageBox.warning(self, "Stock insuffisant",
                                f"Stock disponible : {product['stock_quantity']:.2f}")
            return

        self._cart.append({
            "product_id": product["id"],
            "name": product["name"],
            "unit_price": product["sale_price"],
            "quantity": quantity,
            "unit_type": product["unit_type"],
            "discount": 0.0,
            "stock": product["stock_quantity"],
        })
        self._render_cart()

    def _ask_weight(self, product: dict):
        dlg = WeightDialog(product, self)
        if dlg.exec():
            self._add_to_cart(product, dlg.get_quantity())

    def _render_cart(self):
        while self._cart_layout.count() > 1:
            item = self._cart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, item in enumerate(self._cart):
            row = self._make_cart_row(i, item)
            self._cart_layout.insertWidget(self._cart_layout.count() - 1, row)

        self._update_totals()

    def _make_cart_row(self, idx: int, item: dict) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background: #1E2235; border-radius: 8px;")
        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 8, 10, 8)

        info = QVBoxLayout()
        name = QLabel(item["name"])
        name.setStyleSheet("font-weight: 600; font-size: 13px;")
        unit_label = "kg" if item["unit_type"] == "kg" else ("L" if item["unit_type"] == "litre" else "u")
        sub = QLabel(f"{format_price(item['unit_price'])} / {unit_label}")
        sub.setStyleSheet("color: #9AA0C4; font-size: 11px;")
        info.addWidget(name)
        info.addWidget(sub)

        # Qty control
        qty_row = QHBoxLayout()
        btn_m = QPushButton("−")
        btn_m.setObjectName("btnIcon")
        btn_m.setFixedSize(28, 28)
        btn_m.clicked.connect(lambda _, i=idx: self._change_qty(i, -1 if self._cart[i]["unit_type"] == "piece" else -0.1))

        qty_lbl = QLabel(f"{item['quantity']:.2f}")
        qty_lbl.setAlignment(Qt.AlignCenter)
        qty_lbl.setMinimumWidth(50)
        qty_lbl.setStyleSheet("font-weight: 600;")

        btn_p = QPushButton("＋")
        btn_p.setObjectName("btnIcon")
        btn_p.setFixedSize(28, 28)
        btn_p.clicked.connect(lambda _, i=idx: self._change_qty(i, 1 if self._cart[i]["unit_type"] == "piece" else 0.1))

        qty_row.addWidget(btn_m)
        qty_row.addWidget(qty_lbl)
        qty_row.addWidget(btn_p)

        total_lbl = QLabel(format_price(item["unit_price"] * item["quantity"]))
        total_lbl.setStyleSheet("font-weight: 700; color: #7B8CDE; min-width: 90px;")
        total_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        btn_del = QPushButton("🗑")
        btn_del.setObjectName("btnIcon")
        btn_del.setStyleSheet("color: #E53935;")
        btn_del.clicked.connect(lambda _, i=idx: self._remove_item(i))

        row.addLayout(info, 1)
        row.addLayout(qty_row)
        row.addWidget(total_lbl)
        row.addWidget(btn_del)
        return frame

    def _change_qty(self, idx: int, delta: float):
        item = self._cart[idx]
        new_qty = round(item["quantity"] + delta, 2)
        if new_qty <= 0:
            self._remove_item(idx)
            return
        if new_qty > item["stock"]:
            QMessageBox.warning(self, "Stock insuffisant", f"Stock max: {item['stock']:.2f}")
            return
        item["quantity"] = new_qty
        self._render_cart()

    def _remove_item(self, idx: int):
        self._cart.pop(idx)
        self._render_cart()

    def _clear_cart(self):
        if self._cart and QMessageBox.question(self, "Vider le panier", "Vider le panier ?",
                                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._cart.clear()
            self._render_cart()

    def _update_totals(self):
        subtotal = sum(i["unit_price"] * i["quantity"] for i in self._cart)
        discount = self._discount_spin.value()
        total = max(0, subtotal - discount)
        self._subtotal_lbl.setText(f"Sous-total : {format_price(subtotal)}")
        if discount:
            self._discount_lbl.setText(f"Remise : -{format_price(discount)}")
        else:
            self._discount_lbl.setText("")
        self._total_lbl.setText(f"TOTAL : {format_price(total)}")

    # ── Checkout ──────────────────────────────────────────────

    def _checkout(self, payment_method: str):
        if not self._cart:
            QMessageBox.information(self, "Panier vide", "Ajoutez des produits au panier.")
            return

        subtotal = sum(i["unit_price"] * i["quantity"] for i in self._cart)
        discount = self._discount_spin.value()
        total = max(0, subtotal - discount)

        dlg = PaymentDialog(total, payment_method, self)
        if not dlg.exec():
            return

        amount_paid = dlg.get_amount_paid()
        items = [
            {"product_id": i["product_id"], "quantity": i["quantity"],
             "unit_price": i["unit_price"], "discount": i.get("discount", 0)}
            for i in self._cart
        ]
        settings = {r["key"]: r["value"] for r in db.fetchall("SELECT key, value FROM settings")}

        try:
            sale = SaleController.create_sale(
                items, payment_method, discount, 0, amount_paid,
            )
            self._cart.clear()
            self._discount_spin.setValue(0)
            self._render_cart()

            reply = QMessageBox.question(
                self, "Vente enregistrée",
                f"Vente #{sale['id']} enregistrée.\nTotal : {format_price(sale['total'])}\nMonnaie : {format_price(sale['change_given'])}\n\nImprimer le ticket ?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                pdf_path = generate_receipt_pdf(sale, settings)
                try:
                    if sys.platform == "linux":
                        subprocess.Popen(["xdg-open", pdf_path])
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", pdf_path])
                    else:
                        subprocess.Popen(["start", pdf_path], shell=True)
                except Exception:
                    QMessageBox.information(self, "Ticket", f"Ticket sauvegardé :\n{pdf_path}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


class WeightDialog(QDialog):
    def __init__(self, product: dict, parent=None):
        super().__init__(parent)
        self._product = product
        self.setWindowTitle(f"Quantité — {product['name']}")
        self.setFixedWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        unit = "kg" if product["unit_type"] == "kg" else "L"
        layout.addWidget(QLabel(f"<b>{product['name']}</b>"))
        layout.addWidget(QLabel(f"Prix : {format_price(product['sale_price'])} / {unit}"))

        form = QFormLayout()
        self._qty = QDoubleSpinBox()
        self._qty.setMinimumHeight(48)
        self._qty.setMinimum(0.001)
        self._qty.setMaximum(9999)
        self._qty.setDecimals(3)
        self._qty.setValue(1.0)
        self._qty.setSuffix(f"  {unit}")
        form.addRow("Quantité :", self._qty)
        layout.addLayout(form)

        self._total_lbl = QLabel()
        self._total_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #7B8CDE;")
        self._total_lbl.setAlignment(Qt.AlignCenter)
        self._qty.valueChanged.connect(self._update_total)
        self._update_total()
        layout.addWidget(self._total_lbl)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("✅  Ajouter")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _update_total(self):
        total = self._qty.value() * self._product["sale_price"]
        self._total_lbl.setText(f"Total : {format_price(total)}")

    def get_quantity(self) -> float:
        return self._qty.value()


class PaymentDialog(QDialog):
    def __init__(self, total: float, method: str, parent=None):
        super().__init__(parent)
        self._total = total
        self.setWindowTitle("Paiement")
        self.setFixedWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(QLabel(f"Montant à payer :"))
        lbl = QLabel(format_price(total))
        lbl.setStyleSheet("font-size: 28px; font-weight: 700; color: #7B8CDE;")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        if method == "cash":
            form = QFormLayout()
            self._paid = QDoubleSpinBox()
            self._paid.setMinimumHeight(48)
            self._paid.setMaximum(999999)
            self._paid.setDecimals(3)
            self._paid.setValue(total)
            self._paid.setSuffix("  TND")
            self._paid.valueChanged.connect(self._update_change)
            form.addRow("Montant reçu :", self._paid)
            layout.addLayout(form)

            self._change_lbl = QLabel("Monnaie : 0.000 TND")
            self._change_lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #43A047;")
            self._change_lbl.setAlignment(Qt.AlignCenter)
            self._update_change()
            layout.addWidget(self._change_lbl)
        else:
            self._paid = None
            layout.addWidget(QLabel("Paiement par carte — montant exact."))

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("✅  Valider")
        btn_ok.setObjectName("btnSuccess")
        btn_ok.clicked.connect(self._validate)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _update_change(self):
        change = max(0, self._paid.value() - self._total)
        self._change_lbl.setText(f"Monnaie : {format_price(change)}")

    def _validate(self):
        if self._paid and self._paid.value() < self._total:
            QMessageBox.warning(self, "Montant insuffisant", "Le montant reçu est inférieur au total.")
            return
        self.accept()

    def get_amount_paid(self) -> float:
        return self._paid.value() if self._paid else self._total
