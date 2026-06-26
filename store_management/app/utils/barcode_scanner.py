from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap

try:
    import cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

try:
    from pyzbar import pyzbar
    _PYZBAR_OK = True
except ImportError:
    _PYZBAR_OK = False

SCANNER_AVAILABLE = _CV2_OK and _PYZBAR_OK


class BarcodeScannerDialog(QDialog):
    """Camera barcode / QR-code scanner dialog.

    Opens the default webcam, decodes the first barcode found, and
    returns it via ``get_result()``.  Falls back to manual entry if
    the libraries are missing.
    """

    barcode_detected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scanner code-barres — Caméra")
        self.setMinimumSize(540, 480)
        self.setModal(True)

        self._cap = None
        self._result = ""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_frame)

        self._build_ui()

        if SCANNER_AVAILABLE:
            self._start_camera()
        else:
            self._show_fallback()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setObjectName("scannerHeader")
        hdr.setStyleSheet("background: #00C48C; padding: 12px 20px;")
        hdr.setFixedHeight(56)
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel("📷  Scanner code-barres")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: white; background: transparent;")
        hdr_layout.addWidget(title)
        layout.addWidget(hdr)

        # Camera feed
        self._camera_label = QLabel()
        self._camera_label.setAlignment(Qt.AlignCenter)
        self._camera_label.setMinimumSize(540, 340)
        self._camera_label.setStyleSheet("background: #0E1117; color: #64748B; font-size: 14px;")
        self._camera_label.setText("Initialisation caméra…")
        layout.addWidget(self._camera_label, 1)

        # Status bar
        self._status = QLabel("Pointez un code-barres vers la caméra")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 6px;")
        layout.addWidget(self._status)

        # Manual entry fallback
        manual_frame = QFrame()
        manual_frame.setStyleSheet("background: #161C27; border-top: 1px solid #1E2D3D; padding: 12px;")
        manual_layout = QHBoxLayout(manual_frame)
        manual_layout.setContentsMargins(16, 8, 16, 8)
        manual_lbl = QLabel("Saisie manuelle :")
        manual_lbl.setStyleSheet("color: #94A3B8; font-size: 13px; background: transparent;")
        self._manual_input = QLineEdit()
        self._manual_input.setPlaceholderText("Entrer le code-barres manuellement…")
        self._manual_input.setMinimumHeight(38)
        self._manual_input.returnPressed.connect(self._manual_confirm)
        btn_manual = QPushButton("Valider")
        btn_manual.setMinimumHeight(38)
        btn_manual.clicked.connect(self._manual_confirm)
        manual_layout.addWidget(manual_lbl)
        manual_layout.addWidget(self._manual_input, 1)
        manual_layout.addWidget(btn_manual)
        layout.addWidget(manual_frame)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(16, 8, 16, 12)
        btn_cancel = QPushButton("Fermer")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self._on_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _start_camera(self):
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._camera_label.setText("Aucune caméra détectée.\nUtilisez la saisie manuelle ci-dessous.")
            self._status.setText("Caméra non disponible")
            return
        self._timer.start(33)  # ~30 fps

    def _process_frame(self):
        if not self._cap or not self._cap.isOpened():
            return

        ret, frame = self._cap.read()
        if not ret:
            return

        # Decode barcodes
        barcodes = pyzbar.decode(frame)
        for bc in barcodes:
            # Draw rectangle around barcode
            x, y, w, h = bc.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 196, 140), 3)
            data = bc.data.decode("utf-8", errors="replace")
            cv2.putText(frame, data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 196, 140), 2)
            self._finish(data)
            return

        # Convert to Qt pixmap
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self._camera_label.setPixmap(
            QPixmap.fromImage(img).scaled(
                self._camera_label.width(), self._camera_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
        )

    def _show_fallback(self):
        self._camera_label.setText(
            "Modules manquants : opencv-python et pyzbar requis.\n\n"
            "Installez avec :\n"
            "pip install opencv-python pyzbar\n\n"
            "Utilisez la saisie manuelle ci-dessous."
        )
        self._status.setText("Saisie manuelle disponible")

    def _manual_confirm(self):
        code = self._manual_input.text().strip()
        if code:
            self._finish(code)

    def _finish(self, code: str):
        self._result = code
        self._stop_camera()
        self.accept()

    def _on_cancel(self):
        self._stop_camera()
        self.reject()

    def _stop_camera(self):
        self._timer.stop()
        if self._cap:
            self._cap.release()
            self._cap = None

    def get_result(self) -> str:
        return self._result

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)
