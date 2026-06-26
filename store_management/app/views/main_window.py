import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QMessageBox, QApplication,
    QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from app.controllers.auth_controller import AuthController
from app.views.dashboard_view   import DashboardView
from app.views.pos_view         import POSView
from app.views.products_view    import ProductsView
from app.views.categories_view  import CategoriesView
from app.views.suppliers_view   import SuppliersView
from app.views.stock_view       import StockView
from app.views.sales_view       import SalesView
from app.views.users_view       import UsersView
from app.views.expenses_view    import ExpensesView
from app.views.settings_view    import SettingsView
from config import APP_NAME, APP_VERSION, ASSETS_DIR


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1280, 800)
        self._pages: dict[str, QWidget] = {}
        self._nav_buttons: dict[str, QPushButton] = {}
        self._current_page = ""
        self._build_ui()
        self._apply_theme("dark")
        self._navigate("dashboard")

        # Auto-backup every 24h
        self._backup_timer = QTimer(self)
        self._backup_timer.timeout.connect(self._auto_backup)
        self._backup_timer.start(86_400_000)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ─────────────────────────────────────────
        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(16, 20, 16, 8)
        logo_icon = QLabel("🏪")
        logo_icon.setStyleSheet("font-size: 36px;")
        logo_title = QLabel(APP_NAME)
        logo_title.setObjectName("sidebarTitle")
        logo_version = QLabel(f"v{APP_VERSION}")
        logo_version.setObjectName("sidebarVersion")
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_title)
        logo_layout.addWidget(logo_version)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)

        sidebar_layout.addWidget(logo_widget)
        sidebar_layout.addWidget(sep)

        # Navigation items
        nav_items = [
            ("dashboard",  "📊", "Tableau de bord",    True),
            ("pos",        "🛒", "Caisse (POS)",       True),
            ("products",   "📦", "Produits",           True),
            ("categories", "🏷️", "Catégories",         True),
            ("suppliers",  "🚚", "Fournisseurs",        True),
            ("stock",      "📋", "Gestion du stock",   True),
            ("sales",      "💰", "Historique ventes",  True),
            ("expenses",   "💸", "Dépenses",           True),
            ("users",      "👤", "Utilisateurs",       False),  # Admin only
            ("settings",   "⚙️", "Paramètres",         False),  # Admin only
        ]

        nav_scroll_widget = QWidget()
        nav_layout = QVBoxLayout(nav_scroll_widget)
        nav_layout.setContentsMargins(0, 8, 0, 8)
        nav_layout.setSpacing(2)

        for page_id, icon, label, all_roles in nav_items:
            if not all_roles and not AuthController.is_admin():
                continue
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(46)
            btn.clicked.connect(lambda _, pid=page_id: self._navigate(pid))
            self._nav_buttons[page_id] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        sidebar_layout.addWidget(nav_scroll_widget, 1)

        # User info at bottom of sidebar
        user_frame = QFrame()
        user_frame.setStyleSheet("background: #0E1018; border-top: 1px solid #2D3055;")
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(12, 10, 12, 10)

        user = AuthController.current_user()
        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 24px;")
        info = QVBoxLayout()
        name_lbl = QLabel(user.get("full_name", ""))
        name_lbl.setStyleSheet("font-weight: 600; font-size: 13px;")
        role_lbl = QLabel("Administrateur" if user.get("role") == "admin" else "Caissier")
        role_lbl.setStyleSheet("color: #9AA0C4; font-size: 11px;")
        info.addWidget(name_lbl)
        info.addWidget(role_lbl)

        btn_logout = QPushButton("⏻")
        btn_logout.setObjectName("btnIcon")
        btn_logout.setToolTip("Déconnexion")
        btn_logout.clicked.connect(self._logout)

        user_layout.addWidget(avatar)
        user_layout.addLayout(info, 1)
        user_layout.addWidget(btn_logout)
        sidebar_layout.addWidget(user_frame)

        root.addWidget(self._sidebar)

        # ── Main content area ─────────────────────────────
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top bar
        self._topbar = QFrame()
        self._topbar.setObjectName("topBar")
        topbar_layout = QHBoxLayout(self._topbar)
        topbar_layout.setContentsMargins(20, 0, 20, 0)

        self._page_title = QLabel("Tableau de bord")
        self._page_title.setObjectName("pageTitle")
        topbar_layout.addWidget(self._page_title)
        topbar_layout.addStretch()

        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet("color: #9AA0C4; font-size: 13px;")
        topbar_layout.addWidget(self._clock_lbl)
        content_layout.addWidget(self._topbar)

        # Stacked pages
        self._stack = QStackedWidget()
        content_layout.addWidget(self._stack, 1)
        root.addWidget(content_area, 1)

        # Clock
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _navigate(self, page_id: str):
        if page_id not in self._pages:
            self._pages[page_id] = self._create_page(page_id)
            self._stack.addWidget(self._pages[page_id])

        self._stack.setCurrentWidget(self._pages[page_id])
        self._current_page = page_id

        titles = {
            "dashboard": "📊  Tableau de bord",
            "pos":        "🛒  Caisse — Point de Vente",
            "products":   "📦  Gestion des produits",
            "categories": "🏷️  Catégories",
            "suppliers":  "🚚  Fournisseurs",
            "stock":      "📋  Gestion du stock",
            "sales":      "💰  Historique des ventes",
            "expenses":   "💸  Dépenses",
            "users":      "👤  Gestion des utilisateurs",
            "settings":   "⚙️  Paramètres",
        }
        self._page_title.setText(titles.get(page_id, page_id))

        for pid, btn in self._nav_buttons.items():
            btn.setChecked(pid == page_id)

    def _create_page(self, page_id: str) -> QWidget:
        if page_id == "dashboard":
            return DashboardView()
        elif page_id == "pos":
            return POSView()
        elif page_id == "products":
            return ProductsView()
        elif page_id == "categories":
            return CategoriesView()
        elif page_id == "suppliers":
            return SuppliersView()
        elif page_id == "stock":
            return StockView()
        elif page_id == "sales":
            return SalesView()
        elif page_id == "expenses":
            return ExpensesView()
        elif page_id == "users":
            return UsersView()
        elif page_id == "settings":
            return SettingsView(on_theme_change=self._apply_theme)
        return QWidget()

    def _apply_theme(self, theme: str):
        qss_path = ASSETS_DIR / "themes" / f"{theme}.qss"
        if qss_path.exists():
            QApplication.instance().setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def _update_clock(self):
        from datetime import datetime
        self._clock_lbl.setText(datetime.now().strftime("  %d/%m/%Y   %H:%M:%S"))

    def _logout(self):
        reply = QMessageBox.question(self, "Déconnexion", "Voulez-vous vous déconnecter ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            AuthController.logout()
            from app.views.login_dialog import LoginDialog
            login = LoginDialog()
            if login.exec():
                self._pages.clear()
                while self._stack.count():
                    self._stack.removeWidget(self._stack.widget(0))
                self._rebuild_nav()
                self._navigate("dashboard")
            else:
                QApplication.quit()

    def _rebuild_nav(self):
        pass

    def _auto_backup(self):
        try:
            from app.database.backup import create_backup
            create_backup()
        except Exception:
            pass
