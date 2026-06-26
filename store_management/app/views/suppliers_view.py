from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QMessageBox,
)
from app.views.widgets.search_bar import SearchBar
from app.views.widgets.data_table import DataTable
from app.controllers.supplier_controller import SupplierController


class SuppliersView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        toolbar = QHBoxLayout()
        self._search = SearchBar("🔍  Rechercher un fournisseur...")
        self._search.setMinimumHeight(42)
        self._search.search_changed.connect(self._filter)
        btn_add = QPushButton("＋  Nouveau fournisseur")
        btn_add.clicked.connect(self._add)
        toolbar.addWidget(self._search, 1)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        self._table = DataTable(["ID", "Nom", "Téléphone", "Email", "Adresse"])
        self._table.itemDoubleClicked.connect(self._edit)
        layout.addWidget(self._table, 1)

        btn_row = QHBoxLayout()
        btn_edit = QPushButton("✏️  Modifier")
        btn_edit.setObjectName("btnSecondary")
        btn_edit.clicked.connect(self._edit)
        btn_del = QPushButton("🗑️  Supprimer")
        btn_del.setObjectName("btnDanger")
        btn_del.clicked.connect(self._delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

    def refresh(self):
        self._all = SupplierController.get_all()
        self._table.set_data(self._all, ["id", "name", "phone", "email", "address"])

    def _filter(self, q: str):
        q = q.lower()
        filtered = [s for s in self._all if q in s["name"].lower() or q in (s.get("phone") or "").lower()]
        self._table.set_data(filtered, ["id", "name", "phone", "email", "address"])

    def _add(self):
        dlg = SupplierDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self):
        data = self._table.selected_row_data()
        if not data:
            return
        dlg = SupplierDialog(self, data)
        if dlg.exec():
            self.refresh()

    def _delete(self):
        data = self._table.selected_row_data()
        if not data:
            return
        reply = QMessageBox.question(self, "Supprimer", f"Supprimer «{data['name']}» ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            SupplierController.delete(data["id"])
            self.refresh()


class SupplierDialog(QDialog):
    def __init__(self, parent=None, sup: dict = None):
        super().__init__(parent)
        self._sup = sup
        self.setWindowTitle("Modifier" if sup else "Nouveau fournisseur")
        self.setFixedWidth(420)
        self._build_ui()
        if sup:
            self._name.setText(sup.get("name", ""))
            self._phone.setText(sup.get("phone") or "")
            self._email.setText(sup.get("email") or "")
            self._address.setText(sup.get("address") or "")
            self._notes.setPlainText(sup.get("notes") or "")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        self._name = QLineEdit()
        self._name.setMinimumHeight(42)
        self._phone = QLineEdit()
        self._phone.setMinimumHeight(42)
        self._email = QLineEdit()
        self._email.setMinimumHeight(42)
        self._address = QLineEdit()
        self._address.setMinimumHeight(42)
        self._notes = QTextEdit()
        self._notes.setMaximumHeight(80)

        form.addRow("Nom *:", self._name)
        form.addRow("Téléphone:", self._phone)
        form.addRow("Email:", self._email)
        form.addRow("Adresse:", self._address)
        form.addRow("Notes:", self._notes)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾  Enregistrer")
        btn_save.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _save(self):
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            return
        data = {
            "name": name, "phone": self._phone.text().strip() or None,
            "email": self._email.text().strip() or None,
            "address": self._address.text().strip() or None,
            "notes": self._notes.toPlainText().strip() or None,
        }
        try:
            if self._sup:
                SupplierController.update(self._sup["id"], data)
            else:
                SupplierController.create(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
