from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "0", icon: str = "📊", color: str = "#7B8CDE", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self._color = color

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        left = QVBoxLayout()
        self._label = QLabel(title)
        self._label.setObjectName("cardLabel")

        self._value = QLabel(value)
        self._value.setObjectName("cardValue")
        self._value.setStyleSheet(f"color: {color};")

        left.addWidget(self._label)
        left.addWidget(self._value)

        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("cardIcon")
        icon_lbl.setStyleSheet(f"font-size: 36px; color: {color};")
        icon_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addLayout(left, 1)
        layout.addWidget(icon_lbl)

    def set_value(self, value: str):
        self._value.setText(value)
