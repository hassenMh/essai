from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame,
)
from PySide6.QtCore import Qt
from app.controllers.auth_controller import AuthController


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion — StoreManager Pro")
        self.setFixedSize(440, 540)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header gradient ──────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #00C48C, stop:1 #007A5A); }"
        )
        header.setFixedHeight(180)
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.setSpacing(6)

        icon = QLabel("🏪")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 56px; background: transparent; border: none;")

        title = QLabel("StoreManager Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: white;"
            "background: transparent; border: none; letter-spacing: 1px;"
        )

        subtitle_hdr = QLabel("Système de gestion de magasin")
        subtitle_hdr.setAlignment(Qt.AlignCenter)
        subtitle_hdr.setStyleSheet(
            "font-size: 12px; color: rgba(255,255,255,0.75);"
            "background: transparent; border: none;"
        )

        h_layout.addWidget(icon)
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle_hdr)
        layout.addWidget(header)

        # ── Form area ─────────────────────────────────────────
        form = QFrame()
        form.setStyleSheet(
            "QFrame { background: #161C27; }"
            "QLabel { background: transparent; border: none; }"
        )
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(40, 32, 40, 32)
        form_layout.setSpacing(12)

        lbl_user = QLabel("Nom d'utilisateur")
        lbl_user.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600; background: transparent;")

        self._username = QLineEdit()
        self._username.setPlaceholderText("Entrez votre identifiant")
        self._username.setMinimumHeight(46)
        self._username.setText("admin")
        self._username.setStyleSheet(
            "background: #0D1520; border: 1.5px solid #1E2D3D; border-radius: 8px;"
            "padding: 10px 14px; color: #E2E8F0; font-size: 14px;"
        )

        lbl_pass = QLabel("Mot de passe")
        lbl_pass.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600; background: transparent;")

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setPlaceholderText("Entrez votre mot de passe")
        self._password.setMinimumHeight(46)
        self._password.setText("admin123")
        self._password.setStyleSheet(
            "background: #0D1520; border: 1.5px solid #1E2D3D; border-radius: 8px;"
            "padding: 10px 14px; color: #E2E8F0; font-size: 14px;"
        )
        self._password.returnPressed.connect(self._do_login)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet(
            "color: #EF4444; font-size: 12px; background: transparent; border: none;"
        )
        self._error_label.setAlignment(Qt.AlignCenter)

        btn = QPushButton("🔐   Se connecter")
        btn.setMinimumHeight(50)
        btn.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "    stop:0 #00C48C, stop:1 #00A876);"
            "  color: #0E1117; border: none; border-radius: 10px;"
            "  font-size: 15px; font-weight: 700; letter-spacing: 0.5px;"
            "}"
            "QPushButton:hover { background: #00D99B; }"
            "QPushButton:pressed { background: #009966; }"
        )
        btn.clicked.connect(self._do_login)

        hint = QLabel("Identifiants par défaut : admin / admin123")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(
            "color: #334155; font-size: 11px; background: transparent; border: none;"
        )

        form_layout.addWidget(lbl_user)
        form_layout.addWidget(self._username)
        form_layout.addSpacing(4)
        form_layout.addWidget(lbl_pass)
        form_layout.addWidget(self._password)
        form_layout.addWidget(self._error_label)
        form_layout.addSpacing(8)
        form_layout.addWidget(btn)
        form_layout.addStretch()
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
