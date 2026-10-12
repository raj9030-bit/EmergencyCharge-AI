"""
Telemetry Metric Card Widget.
Presents individual hardware telemetry metrics with big numbers,
unit badges, and honest 'Unavailable' indicators when restricted.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from emergencycharge.ui.styles import (
    COLOR_ACCENT_AMBER,
    COLOR_ACCENT_BLUE,
    COLOR_ACCENT_GREEN,
    COLOR_ACCENT_RED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class TelemetryCard(QFrame):
    """Reusable metric card for hardware telemetry display."""

    def __init__(self, title: str, unit: str = "", default_val: str = "--", parent=None):
        super().__init__(parent)
        self.setProperty("class", "CardFrame")
        self.setObjectName("TelemetryCard")
        self.setStyleSheet("""
            QFrame#TelemetryCard {
                background-color: #111827;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Header: Title + Optional Icon/Unit
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.badge_label = QLabel(unit)
        self.badge_label.setStyleSheet(f"color: {COLOR_ACCENT_BLUE}; font-size: 10px; font-weight: 600; background: #0D1E3A; border-radius: 4px; padding: 2px 6px;")
        header_layout.addWidget(self.badge_label)
        layout.addLayout(header_layout)

        # Center Value
        self.value_label = QLabel(default_val)
        font_val = QFont("Segoe UI", 18, QFont.Bold)
        self.value_label.setFont(font_val)
        self.value_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(self.value_label)

        # Footer Subtitle / Status note
        self.sub_label = QLabel("")
        self.sub_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
        self.sub_label.setWordWrap(True)
        layout.addWidget(self.sub_label)

    def set_value(
        self,
        value_text: str,
        subtitle: str = "",
        is_available: bool = True,
        status_color: Optional[str] = None
    ):
        """Updates metric value with visual feedback."""
        self.value_label.setText(value_text)
        self.sub_label.setText(subtitle)

        if not is_available or value_text in ("Unavailable", "--", "N/A"):
            self.value_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 15px; font-weight: 600;")
        elif status_color:
            self.value_label.setStyleSheet(f"color: {status_color}; font-size: 18px; font-weight: 700;")
        else:
            self.value_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 18px; font-weight: 700;")
