from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.controllers.auth_controller import AuthController


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion")
        self.setFixedSize(420, 520)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header band
        header = QFrame()
        header.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #00C48C, stop:1 #00875A); border-radius: 0;"
        )
        header.setFixedHeight(170)
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("🏪")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 54px; background: transparent;")

        title = QLabel("StoreManager Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: white; background: transparent; letter-spacing: 1px;")

        h_layout.addWidget(icon)
        h_layout.addWidget(title)
        layout.addWidget(header)

        # Form
        form = QFrame()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(16)

        subtitle = QLabel("Connexion à votre espace")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 15px; color: #64748B; margin-bottom: 8px;")
        form_layout.addWidget(subtitle)

        lbl_user = QLabel("Nom d'utilisateur")
        lbl_user.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")
        self._username = QLineEdit()
        self._username.setPlaceholderText("Entrez votre identifiant")
        self._username.setMinimumHeight(46)
        self._username.setText("admin")

        lbl_pass = QLabel("Mot de passe")
        lbl_pass.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setPlaceholderText("Entrez votre mot de passe")
        self._password.setMinimumHeight(46)
        self._password.setText("admin123")
        self._password.returnPressed.connect(self._do_login)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #EF5350; font-size: 12px;")
        self._error_label.setAlignment(Qt.AlignCenter)

        btn = QPushButton("  Se connecter")
        btn.setMinimumHeight(48)
        btn.setStyleSheet("font-size: 15px; font-weight: 700; border-radius: 10px;")
        btn.clicked.connect(self._do_login)

        form_layout.addWidget(lbl_user)
        form_layout.addWidget(self._username)
        form_layout.addWidget(lbl_pass)
        form_layout.addWidget(self._password)
        form_layout.addWidget(self._error_label)
        form_layout.addSpacing(8)
        form_layout.addWidget(btn)
        form_layout.addStretch()

        hint = QLabel("Accès par défaut : admin / admin123")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #475569; font-size: 11px;")
        form_layout.addWidget(hint)

        layout.addWidget(form)

    def _do_login(self):
        username = self._username.text().strip()
        password = self._password.text()
        if not username or not password:
            self._error_label.setText("Veuillez remplir tous les champs.")
            return
        user = AuthController.login(username, password)
        if user:
            self.accept()
        else:
            self._error_label.setText("Identifiants incorrects. Réessayez.")
            self._password.clear()
            self._password.setFocus()
