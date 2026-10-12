"""
Status Banners for Demo Mode, Emergency Mode, and Safety Alerts.
Prominently communicates hardware mode to uphold user trust and compliance with project rules.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from emergencycharge.core.safety_monitor import AlertLevel, SafetyAlert
from emergencycharge.ui.styles import (
    COLOR_ACCENT_AMBER,
    COLOR_ACCENT_BLUE,
    COLOR_ACCENT_GREEN,
    COLOR_ACCENT_RED,
    COLOR_BG_CARD,
    COLOR_TEXT_PRIMARY,
)


class DemoModeBanner(QFrame):
    """High-visibility banner clearly marking active demo/simulation mode."""

    scenario_changed = Signal(str)
    disable_demo_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #78350F, stop:1 #92400E);
                border: 1px solid #F59E0B;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_label = QLabel("DEMO MODE ACTIVE: SIMULATED HARDWARE READINGS")
        title_label.setStyleSheet("color: #FEF3C7; font-weight: 800; font-size: 12px; letter-spacing: 0.5px;")
        text_layout.addWidget(title_label)

        sub_label = QLabel("Readings below are simulated for testing and demonstration. Physical USB sensors are bypassed.")
        sub_label.setStyleSheet("color: #FDE68A; font-size: 11px;")
        text_layout.addWidget(sub_label)
        layout.addLayout(text_layout)

        layout.addStretch()

        # Scenario selector
        scenario_label = QLabel("Scenario:")
        scenario_label.setStyleSheet("color: #FEF3C7; font-weight: 600; font-size: 11px;")
        layout.addWidget(scenario_label)

        self.scenario_combo = QComboBox()
        self.scenario_combo.setStyleSheet("""
            QComboBox {
                background: #451A03;
                border: 1px solid #F59E0B;
                color: #FEF3C7;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
            }
        """)
        self.scenario_combo.addItem("USB 2.0 (2.5W Bottleneck)", "usb_2_0")
        self.scenario_combo.addItem("USB 3.0 (4.5W Standard)", "usb_3_0")
        self.scenario_combo.addItem("USB-C (15W Fast Charge)", "type_c_15w")
        self.scenario_combo.addItem("USB-PD (27W Fast Charge)", "usb_pd_27w")
        self.scenario_combo.addItem("Low Laptop Battery (14%)", "low_battery")
        self.scenario_combo.addItem("Phone Overheat (42.5°C)", "overheat")
        self.scenario_combo.currentIndexChanged.connect(self._on_scenario_selected)
        layout.addWidget(self.scenario_combo)

        # Exit Demo Button
        self.exit_btn = QPushButton("Switch to Real Hardware")
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background: #B45309;
                color: #FFFFFF;
                border: 1px solid #FBBF24;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: 700;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #D97706;
            }
        """)
        self.exit_btn.clicked.connect(self.disable_demo_clicked.emit)
        layout.addWidget(self.exit_btn)

    def _on_scenario_selected(self, index: int):
        sc_id = self.scenario_combo.currentData()
        if sc_id:
            self.scenario_changed.emit(sc_id)


class EmergencyActiveBanner(QFrame):
    """Banner displayed when Emergency Mode is armed."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #064E3B, stop:1 #065F46);
                border: 1px solid #10B981;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        icon_label = QLabel("⚡")
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        title = QLabel("EMERGENCY CHARGE MODE ENGAGED")
        title.setStyleSheet("color: #D1FAE5; font-weight: 800; font-size: 12px;")
        text_layout.addWidget(title)

        detail = QLabel("USB Port Power Lock Active • Away Mode Armed • Laptop Sleep Prevented")
        detail.setStyleSheet("color: #A7F3D0; font-size: 11px;")
        text_layout.addWidget(detail)
        layout.addLayout(text_layout)

        layout.addStretch()


class SafetyAlertBanner(QFrame):
    """Banner rendering dynamic safety alarms with distinct levels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 6, 12, 6)
        self.layout.setSpacing(10)

        self.icon_label = QLabel("⚠️")
        self.icon_label.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.icon_label)

        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(2)
        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-weight: 800; font-size: 12px;")
        self.text_layout.addWidget(self.title_label)

        self.msg_label = QLabel("")
        self.msg_label.setStyleSheet("font-size: 11px;")
        self.text_layout.addWidget(self.msg_label)
        self.layout.addLayout(self.text_layout)

        self.layout.addStretch()

        self.dismiss_btn = QPushButton("Dismiss")
        self.dismiss_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,0.3);
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10px;
            }
        """)
        self.dismiss_btn.clicked.connect(self.hide)
        self.layout.addWidget(self.dismiss_btn)

    def show_alert(self, alert: SafetyAlert):
        if alert.level == AlertLevel.CRITICAL:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #991B1B);
                    border: 1px solid #EF4444;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            self.icon_label.setText("🚨")
            self.title_label.setStyleSheet("color: #FEE2E2; font-weight: 800; font-size: 12px;")
            self.msg_label.setStyleSheet("color: #FECACA; font-size: 11px;")
        else:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #78350F, stop:1 #92400E);
                    border: 1px solid #F59E0B;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
            """)
            self.icon_label.setText("⚠️")
            self.title_label.setStyleSheet("color: #FEF3C7; font-weight: 800; font-size: 12px;")
            self.msg_label.setStyleSheet("color: #FDE68A; font-size: 11px;")

        self.title_label.setText(f"{alert.title}: {alert.action_required}")
        self.msg_label.setText(alert.message)
        self.show()
