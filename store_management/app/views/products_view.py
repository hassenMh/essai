from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QTextEdit, QDateEdit, QFileDialog, QMessageBox, QFrame,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap

from app.views.widgets.search_bar import SearchBar
from app.views.widgets.data_table import DataTable
from app.controllers.product_controller import ProductController
from app.controllers.category_controller import CategoryController
from app.controllers.supplier_controller import SupplierController
from app.utils.qr_utils import generate_qr, generate_barcode_value
from app.utils.helpers import format_price, format_date
import os


class ProductsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_products = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        self._search = SearchBar("🔍  Rechercher un produit...")
        self._search.search_changed.connect(self._filter)
        self._search.setMinimumHeight(42)

        self._cat_filter = QComboBox()
        self._cat_filter.setMinimumHeight(42)
        self._cat_filter.setMinimumWidth(180)
        self._cat_filter.currentIndexChanged.connect(self._filter)

        btn_add = QPushButton("＋  Nouveau produit")
        btn_add.setMinimumHeight(42)
        btn_add.clicked.connect(self._add_product)

        btn_low = QPushButton("⚠️  Stock faible")
        btn_low.setObjectName("btnWarning")
        btn_low.setMinimumHeight(42)
        btn_low.clicked.connect(self._show_low_stock)

        toolbar.addWidget(self._search, 2)
        toolbar.addWidget(self._cat_filter)
        toolbar.addWidget(btn_low)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        # Table
        self._table = DataTable([
            "ID", "Code/QR", "Nom du produit", "Catégorie",
            "Prix achat", "Prix vente", "Stock", "Unité", "Expiration",
        ])
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(1, 130)
        self._table.setColumnWidth(7, 70)
        self._table.itemDoubleClicked.connect(self._edit_selected)
        layout.addWidget(self._table, 1)

        # Bottom action bar
        action_bar = QHBoxLayout()
        btn_edit = QPushButton("✏️  Modifier")
        btn_edit.setObjectName("btnSecondary")
        btn_edit.clicked.connect(self._edit_selected)

        btn_del = QPushButton("🗑️  Supprimer")
        btn_del.setObjectName("btnDanger")
        btn_del.clicked.connect(self._delete_selected)

        btn_qr = QPushButton("QR Code")
        btn_qr.setObjectName("btnSecondary")
        btn_qr.clicked.connect(self._gen_qr)

        btn_stock = QPushButton("📦  Entrée stock")
        btn_stock.setObjectName("btnSuccess")
        btn_stock.clicked.connect(self._stock_entry)

        self._count_lbl = QLabel()
        self._count_lbl.setStyleSheet("color: #9AA0C4;")

        action_bar.addWidget(self._count_lbl)
        action_bar.addStretch()
        action_bar.addWidget(btn_qr)
        action_bar.addWidget(btn_stock)
        action_bar.addWidget(btn_edit)
        action_bar.addWidget(btn_del)
        layout.addLayout(action_bar)

    def refresh(self):
        self._all_products = ProductController.get_all()
        self._load_categories()
        self._display(self._all_products)

    def _load_categories(self):
        self._cat_filter.blockSignals(True)
        current = self._cat_filter.currentData()
        self._cat_filter.clear()
        self._cat_filter.addItem("Toutes les catégories", None)
        for cat in CategoryController.get_all():
            self._cat_filter.addItem(cat["name"], cat["id"])
        if current:
            idx = self._cat_filter.findData(current)
            if idx >= 0:
                self._cat_filter.setCurrentIndex(idx)
        self._cat_filter.blockSignals(False)

    def _filter(self, *args):
        query = self._search.text().strip().lower()
        cat_id = self._cat_filter.currentData()
        result = self._all_products
        if query:
            result = [p for p in result if query in p["name"].lower() or query in (p.get("barcode") or "").lower()]
        if cat_id:
            result = [p for p in result if p.get("category_id") == cat_id]
        self._display(result)

    def _display(self, products: list):
        self._count_lbl.setText(f"{len(products)} produit(s)")
        keys = ["id", "barcode", "name", "category_name", "purchase_price", "sale_price", "stock_quantity", "unit_type", "expiry_date"]

        display_data = []
        for p in products:
            d = dict(p)
            d["purchase_price"] = format_price(p.get("purchase_price", 0))
            d["sale_price"] = format_price(p.get("sale_price", 0))
            d["stock_quantity"] = f"{p.get('stock_quantity', 0):.2f}"
            d["expiry_date"] = format_date(p.get("expiry_date"))
            d["unit_type"] = {"piece": "Pièce", "kg": "Kg", "litre": "L"}.get(p.get("unit_type"), p.get("unit_type", ""))
            display_data.append(d)

        self._table.set_data(display_data, keys)

    def _add_product(self):
        dlg = ProductDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit_selected(self):
        data = self._table.selected_row_data()
        if not data:
            QMessageBox.information(self, "Sélection", "Veuillez sélectionner un produit.")
            return
        product = ProductController.get_by_id(data["id"])
        dlg = ProductDialog(self, product)
        if dlg.exec():
            self.refresh()

    def _delete_selected(self):
        data = self._table.selected_row_data()
        if not data:
            return
        reply = QMessageBox.question(self, "Confirmation", f"Supprimer «{data['name']}» ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ProductController.delete(data["id"])
            self.refresh()

    def _gen_qr(self):
        data = self._table.selected_row_data()
        if not data:
            return
        path = generate_qr(data.get("barcode") or str(data["id"]), data["id"])
        QMessageBox.information(self, "QR Code", f"QR Code généré:\n{path}")

    def _show_low_stock(self):
        products = ProductController.get_low_stock()
        dlg = LowStockDialog(products, self)
        dlg.exec()

    def _stock_entry(self):
        data = self._table.selected_row_data()
        if not data:
            return
        dlg = StockEntryDialog(data["id"], data["name"], self)
        if dlg.exec():
            self.refresh()


class ProductDialog(QDialog):
    def __init__(self, parent=None, product: dict = None):
        super().__init__(parent)
        self._product = product
        self._image_path = product.get("image_path") if product else None
        self.setWindowTitle("Modifier le produit" if product else "Nouveau produit")
        self.setMinimumWidth(600)
        self._build_ui()
        if product:
            self._populate(product)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel("Modifier le produit" if self._product else "Nouveau produit")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 700; padding: 20px 24px 16px;")
        layout.addWidget(title_lbl)

        sep = QFrame()
        sep.setObjectName("separator")
        layout.addWidget(sep)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.NoFrame)
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._name = QLineEdit()
        self._name.setMinimumHeight(42)
        self._name.setPlaceholderText("Nom du produit *")

        self._barcode = QLineEdit()
        self._barcode.setMinimumHeight(42)
        self._barcode.setPlaceholderText("Laisser vide pour auto-générer")

        self._category = QComboBox()
        self._category.setMinimumHeight(42)
        for cat in CategoryController.get_all():
            self._category.addItem(cat["name"], cat["id"])

        self._supplier = QComboBox()
        self._supplier.setMinimumHeight(42)
        self._supplier.addItem("Aucun", None)
        for sup in SupplierController.get_all():
            self._supplier.addItem(sup["name"], sup["id"])

        self._purchase_price = QDoubleSpinBox()
        self._purchase_price.setMinimumHeight(42)
        self._purchase_price.setMaximum(99999.999)
        self._purchase_price.setDecimals(3)
        self._purchase_price.setSuffix("  TND")

        self._sale_price = QDoubleSpinBox()
        self._sale_price.setMinimumHeight(42)
        self._sale_price.setMaximum(99999.999)
        self._sale_price.setDecimals(3)
        self._sale_price.setSuffix("  TND")

        self._stock = QDoubleSpinBox()
        self._stock.setMinimumHeight(42)
        self._stock.setMaximum(999999)
        self._stock.setDecimals(2)

        self._min_stock = QDoubleSpinBox()
        self._min_stock.setMinimumHeight(42)
        self._min_stock.setMaximum(9999)
        self._min_stock.setDecimals(2)
        self._min_stock.setValue(5)

        self._unit_type = QComboBox()
        self._unit_type.setMinimumHeight(42)
        self._unit_type.addItem("Pièce", "piece")
        self._unit_type.addItem("Kilogramme", "kg")
        self._unit_type.addItem("Litre", "litre")

        self._expiry = QDateEdit()
        self._expiry.setMinimumHeight(42)
        self._expiry.setCalendarPopup(True)
        self._expiry.setSpecialValueText("Pas de date")
        self._expiry.setDate(QDate(2000, 1, 1))
        self._expiry.setMinimumDate(QDate(2000, 1, 1))

        self._description = QTextEdit()
        self._description.setMaximumHeight(80)
        self._description.setPlaceholderText("Description optionnelle...")

        img_row = QHBoxLayout()
        self._img_btn = QPushButton("📷  Choisir une image")
        self._img_btn.setObjectName("btnSecondary")
        self._img_btn.clicked.connect(self._pick_image)
        self._img_lbl = QLabel()
        self._img_lbl.setFixedSize(60, 60)
        self._img_lbl.setStyleSheet("border: 1px solid #2D3055; border-radius: 8px;")
        img_row.addWidget(self._img_btn)
        img_row.addWidget(self._img_lbl)

        form.addRow("Nom *:", self._name)
        form.addRow("Code-barres:", self._barcode)
        form.addRow("Catégorie *:", self._category)
        form.addRow("Fournisseur:", self._supplier)
        form.addRow("Prix d'achat:", self._purchase_price)
        form.addRow("Prix de vente *:", self._sale_price)
        form.addRow("Stock initial:", self._stock)
        form.addRow("Stock minimum:", self._min_stock)
        form.addRow("Unité:", self._unit_type)
        form.addRow("Expiration:", self._expiry)
        form.addRow("Description:", self._description)
        form.addRow("Image:", img_row)

        form_scroll.setWidget(form_widget)
        layout.addWidget(form_scroll, 1)

        sep2 = QFrame()
        sep2.setObjectName("separator")
        layout.addWidget(sep2)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(24, 16, 24, 16)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾  Enregistrer")
        btn_save.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _populate(self, p: dict):
        self._name.setText(p.get("name", ""))
        self._barcode.setText(p.get("barcode") or "")
        idx = self._category.findData(p.get("category_id"))
        if idx >= 0:
            self._category.setCurrentIndex(idx)
        idx = self._supplier.findData(p.get("supplier_id"))
        if idx >= 0:
            self._supplier.setCurrentIndex(idx)
        self._purchase_price.setValue(p.get("purchase_price", 0))
        self._sale_price.setValue(p.get("sale_price", 0))
        self._min_stock.setValue(p.get("min_stock", 5))
        idx = self._unit_type.findData(p.get("unit_type", "piece"))
        if idx >= 0:
            self._unit_type.setCurrentIndex(idx)
        if p.get("expiry_date"):
            self._expiry.setDate(QDate.fromString(p["expiry_date"], "yyyy-MM-dd"))
        self._description.setPlainText(p.get("description") or "")
        self._stock.setEnabled(False)

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Image produit", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self._image_path = path
            pix = QPixmap(path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._img_lbl.setPixmap(pix)

    def _save(self):
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            return
        if self._sale_price.value() <= 0:
            QMessageBox.warning(self, "Erreur", "Le prix de vente doit être supérieur à 0.")
            return

        expiry_str = None
        if self._expiry.date() != QDate(2000, 1, 1):
            expiry_str = self._expiry.date().toString("yyyy-MM-dd")

        data = {
            "name": name,
            "barcode": self._barcode.text().strip() or None,
            "category_id": self._category.currentData(),
            "supplier_id": self._supplier.currentData(),
            "purchase_price": self._purchase_price.value(),
            "sale_price": self._sale_price.value(),
            "stock_quantity": self._stock.value(),
            "min_stock": self._min_stock.value(),
            "unit_type": self._unit_type.currentData(),
            "expiry_date": expiry_str,
            "description": self._description.toPlainText().strip() or None,
            "image_path": self._image_path,
        }

        try:
            if self._product:
                ProductController.update(self._product["id"], data)
            else:
                pid = ProductController.create(data)
                if not data["barcode"]:
                    bc = generate_barcode_value(pid)
                    from app.database.connection import db
                    db.execute("UPDATE products SET barcode=? WHERE id=?", (bc, pid))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


class StockEntryDialog(QDialog):
    def __init__(self, product_id: int, product_name: str, parent=None):
        super().__init__(parent)
        self._product_id = product_id
        self.setWindowTitle("Entrée de stock")
        self.setFixedWidth(380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(QLabel(f"<b>Produit :</b> {product_name}"))

        form = QFormLayout()
        self._qty = QDoubleSpinBox()
        self._qty.setMinimumHeight(42)
        self._qty.setMinimum(0.01)
        self._qty.setMaximum(99999)
        self._qty.setDecimals(2)
        self._qty.setValue(1)

        self._ref = QLineEdit()
        self._ref.setMinimumHeight(42)
        self._ref.setPlaceholderText("N° de livraison, fournisseur...")

        self._notes = QLineEdit()
        self._notes.setMinimumHeight(42)
        self._notes.setPlaceholderText("Remarques optionnelles...")

        form.addRow("Quantité à ajouter *:", self._qty)
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
        from app.controllers.stock_controller import StockController
        StockController.add_stock(self._product_id, self._qty.value(), self._notes.text(), self._ref.text())
        self.accept()


class LowStockDialog(QDialog):
    def __init__(self, products: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Produits en stock faible")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(QLabel(f"<b>{len(products)} produit(s) en stock insuffisant</b>"))
        tbl = DataTable(["Produit", "Catégorie", "Stock actuel", "Stock minimum"])
        tbl.set_data(products, ["name", "category_name", "stock_quantity", "min_stock"])
        layout.addWidget(tbl, 1)
        btn = QPushButton("Fermer")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, 0, Qt.AlignRight)
