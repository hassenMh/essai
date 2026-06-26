from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QLabel, QMessageBox,
    QColorDialog, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.views.widgets.data_table import DataTable
from app.controllers.category_controller import CategoryController


class CategoriesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        toolbar = QHBoxLayout()
        btn_add = QPushButton("＋  Nouvelle catégorie")
        btn_add.clicked.connect(self._add)
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        self._table = DataTable(["ID", "Nom", "Description", "Couleur"])
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
        cats = CategoryController.get_all()
        self._table.set_data(cats, ["id", "name", "description", "color"])

    def _add(self):
        dlg = CategoryDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self):
        data = self._table.selected_row_data()
        if not data:
            return
        dlg = CategoryDialog(self, data)
        if dlg.exec():
            self.refresh()

    def _delete(self):
        data = self._table.selected_row_data()
        if not data:
            return
        try:
            reply = QMessageBox.question(self, "Supprimer", f"Supprimer «{data['name']}» ?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                CategoryController.delete(data["id"])
                self.refresh()
        except ValueError as e:
            QMessageBox.warning(self, "Impossible", str(e))


class CategoryDialog(QDialog):
    def __init__(self, parent=None, cat: dict = None):
        super().__init__(parent)
        self._cat = cat
        self._color = cat["color"] if cat else "#4CAF50"
        self.setWindowTitle("Modifier" if cat else "Nouvelle catégorie")
        self.setFixedWidth(380)
        self._build_ui()
        if cat:
            self._name.setText(cat["name"])
            self._desc.setPlainText(cat.get("description") or "")
            self._update_color_btn()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        self._name = QLineEdit()
        self._name.setMinimumHeight(42)
        self._desc = QTextEdit()
        self._desc.setMaximumHeight(80)

        self._color_btn = QPushButton("  Choisir une couleur")
        self._color_btn.setObjectName("btnSecondary")
        self._color_btn.clicked.connect(self._pick_color)
        self._update_color_btn()

        form.addRow("Nom *:", self._name)
        form.addRow("Description:", self._desc)
        form.addRow("Couleur:", self._color_btn)
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

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self._update_color_btn()

    def _update_color_btn(self):
        self._color_btn.setStyleSheet(f"background: {self._color}; color: white; border-radius: 8px;")

    def _save(self):
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            return
        try:
            if self._cat:
                CategoryController.update(self._cat["id"], name, self._desc.toPlainText(), self._color)
            else:
                CategoryController.create(name, self._desc.toPlainText(), self._color)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
