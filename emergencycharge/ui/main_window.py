"""
Master Window for EmergencyCharge AI.
Orchestrates dashboard telemetry, emergency power locking, AI advisor,
hardware simulator, and real-time visualization.
"""

from datetime import datetime
import os
import sys
from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from emergencycharge.ai.llm_advisor import HybridAIAdvisor
from emergencycharge.config import (
    APP_TITLE,
    DEFAULT_LAPTOP_RESERVE_PERCENT,
    POLL_INTERVAL_MS,
    USB_SPECS,
    VERSION,
)
from emergencycharge.core.laptop_telemetry import LaptopBatteryInfo, LaptopTelemetryMonitor
from emergencycharge.core.phone_detector import PhoneConnectionInfo, PhoneDetector
from emergencycharge.core.power_estimator import ChargingEstimate, PowerEstimator
from emergencycharge.core.safety_monitor import AlertLevel, SafetyMonitor
from emergencycharge.core.simulator import HardwareSimulator, SCENARIOS
from emergencycharge.core.windows_power import WindowsPowerManager
from emergencycharge.ui.styles import (
    COLOR_ACCENT_AMBER,
    COLOR_ACCENT_BLUE,
    COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GREEN,
    COLOR_ACCENT_RED,
    COLOR_BG_CARD,
    COLOR_BORDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    MAIN_STYLESHEET,
)
from emergencycharge.ui.widgets.battery_gauge import CircularBatteryGauge, HorizontalBatteryBar
from emergencycharge.ui.widgets.physics_dialog import PhysicsReportDialog
from emergencycharge.ui.widgets.power_chart import RealtimePowerChart
from emergencycharge.ui.widgets.status_banner import (
    DemoModeBanner,
    EmergencyActiveBanner,
    SafetyAlertBanner,
)
from emergencycharge.ui.widgets.telemetry_card import TelemetryCard


class MainWindow(QMainWindow):
    """Main application window for EmergencyCharge AI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} v{VERSION} — Laptop-to-Phone Emergency Charging Optimizer")
        self.resize(1140, 800)
        self.setMinimumSize(960, 680)
        self.setStyleSheet(MAIN_STYLESHEET)

        # Core subsystems
        self.laptop_monitor = LaptopTelemetryMonitor()
        self.phone_detector = PhoneDetector()
        self.power_estimator = PowerEstimator()
        self.power_manager = WindowsPowerManager()
        self.safety_monitor = SafetyMonitor(DEFAULT_LAPTOP_RESERVE_PERCENT)
        self.simulator = HardwareSimulator()
        self.ai_advisor = HybridAIAdvisor()

        # State flags
        self.is_demo_mode = False
        self.is_emergency_mode = False
        self.selected_port_spec = "USB_3_0"

        # Cached telemetry
        self.last_laptop_info: Optional[LaptopBatteryInfo] = None
        self.last_phone_info: Optional[PhoneConnectionInfo] = None
        self.last_estimate: Optional[ChargingEstimate] = None

        self._setup_ui()

        # Telemetry Polling Timer
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._poll_telemetry)
        self.poll_timer.start(POLL_INTERVAL_MS)

        # Initial tick
        self._poll_telemetry()
        self._log_event("Application initialized. Hardware monitoring active.")

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 14, 18, 16)
        main_layout.setSpacing(10)

        # 1. Top Bar
        main_layout.addLayout(self._build_top_bar())

        # 2. Banners Area
        self.demo_banner = DemoModeBanner()
        self.demo_banner.scenario_changed.connect(self._on_sim_scenario_changed)
        self.demo_banner.disable_demo_clicked.connect(self._toggle_demo_mode)
        self.demo_banner.hide()
        main_layout.addWidget(self.demo_banner)

        self.emergency_banner = EmergencyActiveBanner()
        self.emergency_banner.hide()
        main_layout.addWidget(self.emergency_banner)

        self.alert_banner = SafetyAlertBanner()
        main_layout.addWidget(self.alert_banner)

        # 3. Main Workspace Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_dashboard_tab(), "⚡ SMART DASHBOARD")
        self.tabs.addTab(self._build_emergency_mode_tab(), "🛡️ EMERGENCY MODE")
        self.tabs.addTab(self._build_ai_assistant_tab(), "🤖 AI CHARGING ASSISTANT")
        self.tabs.addTab(self._build_diagnostics_tab(), "📋 HARDWARE LOG & DIAGNOSTICS")

        main_layout.addWidget(self.tabs, stretch=1)

    def _build_top_bar(self) -> QHBoxLayout:
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 4)
        top_layout.setSpacing(14)

        # App Logo & Branding
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(2)

        app_title = QLabel(f"⚡ {APP_TITLE.upper()}")
        app_title.setStyleSheet(f"color: {COLOR_ACCENT_BLUE}; font-size: 19px; font-weight: 900; letter-spacing: 0.5px;")
        logo_layout.addWidget(app_title)

        app_sub = QLabel("AI-Powered Laptop-to-Phone Emergency Charging Optimizer")
        app_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 500;")
        logo_layout.addWidget(app_sub)
        top_layout.addLayout(logo_layout)

        top_layout.addStretch()

        # Laptop Battery Telemetry Pill
        self.laptop_pill = QFrame()
        self.laptop_pill.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 6px 14px;
            }}
        """)
        pill_layout = QHBoxLayout(self.laptop_pill)
        pill_layout.setContentsMargins(8, 4, 8, 4)
        pill_layout.setSpacing(10)

        self.laptop_icon_label = QLabel("💻")
        self.laptop_icon_label.setStyleSheet("font-size: 16px;")
        pill_layout.addWidget(self.laptop_icon_label)

        v_bat = QVBoxLayout()
        v_bat.setSpacing(2)
        h_info = QHBoxLayout()
        self.laptop_pct_label = QLabel("Laptop: --%")
        self.laptop_pct_label.setStyleSheet("font-weight: 800; font-size: 12px; color: #F8FAFC;")
        h_info.addWidget(self.laptop_pct_label)

        self.laptop_source_label = QLabel("Battery")
        self.laptop_source_label.setStyleSheet(f"font-size: 10px; color: {COLOR_TEXT_SECONDARY};")
        h_info.addWidget(self.laptop_source_label)
        v_bat.addLayout(h_info)

        self.laptop_bar = HorizontalBatteryBar()
        v_bat.addWidget(self.laptop_bar)
        pill_layout.addLayout(v_bat)

        self.laptop_discharge_label = QLabel("-- W")
        self.laptop_discharge_label.setStyleSheet(f"font-weight: 800; font-size: 12px; color: {COLOR_ACCENT_AMBER};")
        pill_layout.addWidget(self.laptop_discharge_label)

        top_layout.addWidget(self.laptop_pill)

        # Demo Mode Toggle Button
        self.demo_toggle_btn = QPushButton("🎮 Demo Mode: OFF")
        self.demo_toggle_btn.setToolTip("Toggle simulated hardware profiles for demonstration & testing without a physical phone")
        self.demo_toggle_btn.clicked.connect(self._toggle_demo_mode)
        top_layout.addWidget(self.demo_toggle_btn)

        # Physics & Engineering Report Button
        self.physics_btn = QPushButton("🔬 Physics & Hardware Limits")
        self.physics_btn.setToolTip("View full engineering investigation on USB limits and software boundaries")
        self.physics_btn.clicked.connect(self._open_physics_dialog)
        top_layout.addWidget(self.physics_btn)

        return top_layout

    def _build_dashboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # Left Column: Smartphone Connection Card
        left_card = QFrame()
        left_card.setProperty("class", "CardFrame")
        left_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
        """)
        left_card.setFixedWidth(340)

        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(18, 16, 18, 16)
        left_layout.setSpacing(12)

        left_header = QHBoxLayout()
        left_title = QLabel("CONNECTED SMARTPHONE")
        left_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        left_header.addWidget(left_title)
        left_header.addStretch()

        self.conn_badge = QLabel("DISCONNECTED")
        self.conn_badge.setStyleSheet(f"background: #1E293B; color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 8px;")
        left_header.addWidget(self.conn_badge)
        left_layout.addLayout(left_header)

        # Device Model Title
        self.device_name_label = QLabel("No Smartphone Connected")
        self.device_name_label.setStyleSheet("color: #F8FAFC; font-size: 16px; font-weight: 800;")
        self.device_name_label.setWordWrap(True)
        left_layout.addWidget(self.device_name_label)

        # Circular Battery Gauge
        self.phone_gauge = CircularBatteryGauge()
        left_layout.addWidget(self.phone_gauge, alignment=Qt.AlignCenter)

        # Telemetry Source & Honesty Note
        self.telemetry_notice_label = QLabel(
            "Direct battery percentage & charging wattage require USB debugging on Android. "
            "Standard USB/MTP connects safely but restricts battery register access."
        )
        self.telemetry_notice_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; line-height: 1.4;")
        self.telemetry_notice_label.setWordWrap(True)
        left_layout.addWidget(self.telemetry_notice_label)

        left_layout.addStretch()

        # Port Selection Override (for standard USB ports)
        port_box = QVBoxLayout()
        port_box.setSpacing(4)
        port_lbl = QLabel("Estimated Port Standard:")
        port_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
        port_box.addWidget(port_lbl)

        self.port_select_combo = QComboBox()
        for k, v in USB_SPECS.items():
            self.port_select_combo.addItem(f"{v.name} ({v.power_watts:.1f}W)", k)
        self.port_select_combo.setCurrentIndex(1)  # Default USB 3.0
        self.port_select_combo.currentIndexChanged.connect(self._on_port_spec_changed)
        port_box.addWidget(self.port_select_combo)
        left_layout.addLayout(port_box)

        layout.addWidget(left_card)

        # Right Column: Metrics Grid & Power Flow Chart
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)

        # 6-Card Telemetry Grid
        grid = QGridLayout()
        grid.setSpacing(10)

        self.card_power = TelemetryCard("CHARGING POWER", "WATTS", "-- W")
        grid.addWidget(self.card_power, 0, 0)

        self.card_voltage = TelemetryCard("VOLTAGE", "VOLTS", "-- V")
        grid.addWidget(self.card_voltage, 0, 1)

        self.card_current = TelemetryCard("CURRENT", "MILLIAMPS", "-- mA")
        grid.addWidget(self.card_current, 0, 2)

        self.card_temp = TelemetryCard("BATTERY TEMP", "CELSIUS", "-- °C")
        grid.addWidget(self.card_temp, 1, 0)

        self.card_time = TelemetryCard("ESTIMATED CHARGE TIME", "DURATION", "--")
        grid.addWidget(self.card_time, 1, 1)

        self.card_eff = TelemetryCard("TRANSFER EFFICIENCY", "SYSTEM %", "-- %")
        grid.addWidget(self.card_eff, 1, 2)

        right_layout.addLayout(grid)

        # Real-Time Rolling Power Flow Graph
        chart_card = QFrame()
        chart_card.setProperty("class", "CardFrame")
        chart_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 10, 12, 10)
        chart_layout.setSpacing(6)

        chart_header = QHBoxLayout()
        chart_title = QLabel("REAL-TIME POWER FLOW & LAPTOP DISCHARGE (WATTS)")
        chart_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        chart_header.addWidget(chart_title)
        chart_header.addStretch()
        chart_layout.addLayout(chart_header)

        self.power_chart = RealtimePowerChart()
        chart_layout.addWidget(self.power_chart)
        right_layout.addWidget(chart_card, stretch=1)

        # Hardware Port & Controller Info Bar
        info_bar = QFrame()
        info_bar.setStyleSheet(f"background: #0E1626; border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 6px 12px;")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(8, 4, 8, 4)

        self.hw_info_label = QLabel("Host Controller: Detecting...")
        self.hw_info_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
        info_layout.addWidget(self.hw_info_label)
        info_layout.addStretch()

        self.limits_badge = QLabel("USB-IF Enforced Limits")
        self.limits_badge.setStyleSheet(f"color: {COLOR_ACCENT_BLUE}; font-size: 10px; font-weight: 600;")
        info_layout.addWidget(self.limits_badge)
        right_layout.addWidget(info_bar)

        layout.addLayout(right_layout, stretch=1)
        return widget

    def _build_emergency_mode_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Giant Action Card
        action_card = QFrame()
        action_card.setProperty("class", "CardFrame")
        action_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        ac_layout = QVBoxLayout(action_card)
        ac_layout.setSpacing(14)

        ac_header = QLabel("EMERGENCY CHARGING CONTROLLER")
        ac_header.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 800; letter-spacing: 0.5px;")
        ac_layout.addWidget(ac_header)

        desc = QLabel(
            "In an emergency when no wall outlet is available, Emergency Mode optimizes your laptop's power system "
            "to safely transfer the maximum possible energy into your phone while guarding against laptop battery depletion."
        )
        desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; line-height: 1.5;")
        desc.setWordWrap(True)
        ac_layout.addWidget(desc)

        # Prominent Emergency Engage Button
        self.emergency_btn = QPushButton("⚡ ENGAGE EMERGENCY CHARGE MODE")
        self.emergency_btn.setObjectName("EmergencyButtonInactive")
        self.emergency_btn.setFixedHeight(54)
        self.emergency_btn.clicked.connect(self._toggle_emergency_mode)
        ac_layout.addWidget(self.emergency_btn)

        # Status note
        self.emergency_status_desc = QLabel("Status: Standby. Standard Windows power policies active.")
        self.emergency_status_desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        ac_layout.addWidget(self.emergency_status_desc)

        layout.addWidget(action_card)

        # Settings & Efficiency Row
        row = QHBoxLayout()
        row.setSpacing(14)

        # Left: Laptop Reserve Cutoff Configuration
        cutoff_card = QFrame()
        cutoff_card.setProperty("class", "CardFrame")
        cutoff_card.setStyleSheet(f"background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 14px;")
        cc_layout = QVBoxLayout(cutoff_card)
        cc_layout.setSpacing(10)

        cc_title = QLabel("LAPTOP BATTERY SAFETY RESERVE CUTOFF")
        cc_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 800;")
        cc_layout.addWidget(cc_title)

        cc_desc = QLabel("Stop emergency charging when laptop battery reaches this reserve to prevent leaving you stranded:")
        cc_desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        cc_desc.setWordWrap(True)
        cc_layout.addWidget(cc_desc)

        h_slider = QHBoxLayout()
        self.reserve_slider = QSlider(Qt.Horizontal)
        self.reserve_slider.setRange(10, 50)
        self.reserve_slider.setValue(DEFAULT_LAPTOP_RESERVE_PERCENT)
        self.reserve_slider.valueChanged.connect(self._on_reserve_slider_changed)
        h_slider.addWidget(self.reserve_slider)

        self.reserve_label = QLabel(f"{DEFAULT_LAPTOP_RESERVE_PERCENT}%")
        self.reserve_label.setStyleSheet(f"color: {COLOR_ACCENT_BLUE}; font-weight: 800; font-size: 14px; min-width: 45px;")
        h_slider.addWidget(self.reserve_label)
        cc_layout.addLayout(h_slider)

        self.reserve_progress = QProgressBar()
        self.reserve_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #0E1626;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                text-align: center;
                height: 12px;
                color: #FFFFFF;
                font-size: 10px;
                font-weight: 700;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT_BLUE};
                border-radius: 3px;
            }}
        """)
        self.reserve_progress.setValue(78)
        cc_layout.addWidget(self.reserve_progress)
        row.addWidget(cutoff_card)

        # Right: Efficiency Optimization Checklist
        check_card = QFrame()
        check_card.setProperty("class", "CardFrame")
        check_card.setStyleSheet(f"background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 14px;")
        chk_layout = QVBoxLayout(check_card)
        chk_layout.setSpacing(8)

        chk_title = QLabel("EMERGENCY MAX-EFFICIENCY CHECKLIST")
        chk_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 800;")
        chk_layout.addWidget(chk_title)

        self.chk_keep_awake = QCheckBox("Win32 Away Mode Active (Keeps USB energized with screen off)")
        self.chk_keep_awake.setEnabled(False)
        self.chk_keep_awake.setChecked(False)
        chk_layout.addWidget(self.chk_keep_awake)

        self.chk_screen = QCheckBox("Turn Phone Screen OFF (Saves 2.0W internal drain)")
        self.chk_screen.setChecked(True)
        chk_layout.addWidget(self.chk_screen)

        self.chk_airplane = QCheckBox("Enable Phone Airplane Mode (Halts cellular antenna search)")
        self.chk_airplane.setChecked(True)
        chk_layout.addWidget(self.chk_airplane)

        self.chk_dim_laptop = QCheckBox("Dim Laptop Screen to Minimum (Preserves 5W-8W of laptop battery)")
        self.chk_dim_laptop.setChecked(True)
        chk_layout.addWidget(self.chk_dim_laptop)

        row.addWidget(check_card)
        layout.addLayout(row)

        layout.addStretch()
        return widget

    def _build_ai_assistant_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # Left Column: AI Diagnostics & Action Cards
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)

        diag_card = QFrame()
        diag_card.setProperty("class", "CardFrame")
        diag_card.setStyleSheet(f"background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 14px;")
        dc_layout = QVBoxLayout(diag_card)
        dc_layout.setSpacing(8)

        dc_header = QLabel("AUTOMATED CHARGING BOTTLENECK ANALYSIS")
        dc_header.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 800;")
        dc_layout.addWidget(dc_header)

        self.ai_summary_label = QLabel("Analyzing current hardware state...")
        self.ai_summary_label.setStyleSheet("color: #F8FAFC; font-size: 13px; font-weight: 600;")
        self.ai_summary_label.setWordWrap(True)
        dc_layout.addWidget(self.ai_summary_label)

        self.ai_bottlenecks_label = QLabel("")
        self.ai_bottlenecks_label.setStyleSheet(f"color: {COLOR_ACCENT_AMBER}; font-size: 12px; line-height: 1.4;")
        self.ai_bottlenecks_label.setWordWrap(True)
        dc_layout.addWidget(self.ai_bottlenecks_label)
        left_layout.addWidget(diag_card)

        # Recommended Actions Scroll Area
        act_card = QFrame()
        act_card.setProperty("class", "CardFrame")
        act_card.setStyleSheet(f"background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 14px;")
        act_layout = QVBoxLayout(act_card)
        act_layout.setSpacing(8)

        act_header = QLabel("PRIORITIZED OPTIMIZATION ACTIONS")
        act_header.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 800;")
        act_layout.addWidget(act_header)

        self.actions_scroll = QScrollArea()
        self.actions_scroll.setWidgetResizable(True)
        self.actions_scroll.setStyleSheet("background: transparent; border: none;")

        self.actions_container = QWidget()
        self.actions_vbox = QVBoxLayout(self.actions_container)
        self.actions_vbox.setContentsMargins(0, 0, 0, 0)
        self.actions_vbox.setSpacing(8)
        self.actions_scroll.setWidget(self.actions_container)
        act_layout.addWidget(self.actions_scroll)
        left_layout.addWidget(act_card, stretch=1)

        layout.addLayout(left_layout, stretch=1)

        # Right Column: Interactive AI Chat & Prompt Bar
        chat_card = QFrame()
        chat_card.setProperty("class", "CardFrame")
        chat_card.setStyleSheet(f"background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 14px;")
        chat_layout = QVBoxLayout(chat_card)
        chat_layout.setSpacing(10)

        chat_header = QHBoxLayout()
        chat_title = QLabel("AI CHARGING ASSISTANT (OFFLINE EXPERT + OPTIONAL GEMINI)")
        chat_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 800;")
        chat_header.addWidget(chat_title)
        chat_header.addStretch()

        self.llm_status_badge = QLabel("100% Offline Expert System")
        self.llm_status_badge.setStyleSheet(f"color: {COLOR_ACCENT_GREEN}; font-size: 10px; font-weight: 600; background: #0D261E; padding: 2px 6px; border-radius: 4px;")
        chat_header.addWidget(self.llm_status_badge)
        chat_layout.addLayout(chat_header)

        # Quick Question Buttons
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(6)

        btn_q1 = QPushButton("Why is it slow?")
        btn_q1.clicked.connect(lambda: self._ask_assistant("Why is smartphone charging slow from a laptop?"))
        quick_layout.addWidget(btn_q1)

        btn_q2 = QPushButton("Can software force more current?")
        btn_q2.clicked.connect(lambda: self._ask_assistant("Can Windows software increase USB charging current beyond default hardware limits?"))
        quick_layout.addWidget(btn_q2)

        btn_q3 = QPushButton("How to save laptop battery?")
        btn_q3.clicked.connect(lambda: self._ask_assistant("How can I preserve laptop battery while charging my phone?"))
        quick_layout.addWidget(btn_q3)

        btn_q4 = QPushButton("Cable advice")
        btn_q4.clicked.connect(lambda: self._ask_assistant("How does cable quality affect charging speed?"))
        quick_layout.addWidget(btn_q4)

        chat_layout.addLayout(quick_layout)

        # Response Browser
        self.chat_browser = QTextBrowser()
        self.chat_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: #0B101B;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 12px;
                color: #F8FAFC;
                font-size: 13px;
                line-height: 1.5;
            }}
        """)
        self.chat_browser.setMarkdown(
            "### AI Charging Assistant Ready\n\n"
            "Ask any question about charging bottlenecks, USB-IF power limits, port selection, "
            "or emergency power strategies.\n\n"
            "Click one of the quick question chips above or type a custom question below."
        )
        chat_layout.addWidget(self.chat_browser, stretch=1)

        # Prompt Input Row
        prompt_layout = QHBoxLayout()
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Ask the AI Charging Assistant a question...")
        self.prompt_input.returnPressed.connect(self._on_submit_custom_query)
        prompt_layout.addWidget(self.prompt_input)

        self.ask_btn = QPushButton("Ask Assistant")
        self.ask_btn.setStyleSheet(f"background: {COLOR_ACCENT_BLUE}; color: #090D16; font-weight: 700;")
        self.ask_btn.clicked.connect(self._on_submit_custom_query)
        prompt_layout.addWidget(self.ask_btn)
        chat_layout.addLayout(prompt_layout)

        # Optional Gemini API Key Collapsible / Field
        api_layout = QHBoxLayout()
        api_lbl = QLabel("Optional Gemini API Key:")
        api_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        api_layout.addWidget(api_lbl)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Paste Google Gemini key (optional - offline system works without it)")
        self.api_key_input.textChanged.connect(self._on_api_key_changed)
        api_layout.addWidget(self.api_key_input)
        chat_layout.addLayout(api_layout)

        layout.addWidget(chat_card, stretch=1)
        return widget

    def _build_diagnostics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        lbl = QLabel("SYSTEM & HARDWARE EVENT LOG")
        lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: 800;")
        header_layout.addWidget(lbl)
        header_layout.addStretch()

        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(lambda: self.log_browser.clear())
        header_layout.addWidget(clear_btn)
        layout.addLayout(header_layout)

        self.log_browser = QTextBrowser()
        self.log_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: #070B12;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 12px;
                color: #A7F3D0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.log_browser, stretch=1)

        return widget

    # -------------------------------------------------------------
    # Telemetry Polling & Core Logic
    # -------------------------------------------------------------
    def _poll_telemetry(self):
        """Main periodic loop polling laptop telemetry, phone detection, and safety rules."""
        # 1. Fetch Laptop Telemetry
        if self.is_demo_mode:
            laptop_info = self.simulator.get_laptop_telemetry()
            phone_info = self.simulator.get_phone_info()
        else:
            laptop_info = self.laptop_monitor.get_telemetry()
            phone_info = self.phone_detector.detect()

        self.last_laptop_info = laptop_info
        self.last_phone_info = phone_info

        # 2. Update Laptop Pill in Top Bar
        self.laptop_pct_label.setText(f"Laptop: {laptop_info.percent:.0f}%")
        self.laptop_source_label.setText(
            "AC Mains" if laptop_info.is_plugged else f"{laptop_info.secs_left // 60 if laptop_info.secs_left else '--'}m left"
        )
        self.laptop_bar.update_state(laptop_info.percent, laptop_info.is_plugged)
        if laptop_info.discharge_rate_w is not None and laptop_info.discharge_rate_w > 0:
            self.laptop_discharge_label.setText(f"-{laptop_info.discharge_rate_w:.1f} W")
        else:
            self.laptop_discharge_label.setText("0.0 W" if laptop_info.is_plugged else "-- W")

        # Update Emergency Reserve Progress
        self.reserve_progress.setValue(int(laptop_info.percent))

        # 3. Compute Power Estimate
        port_key = self.selected_port_spec
        estimate = self.power_estimator.calculate_estimate(
            phone_percent=phone_info.battery_percent,
            measured_power_w=phone_info.charging_power_w,
            port_spec_key=port_key,
            laptop_discharge_w=laptop_info.discharge_rate_w,
            phone_screen_on=not self.chk_screen.isChecked(),
            is_simulated=self.is_demo_mode
        )
        self.last_estimate = estimate

        # 4. Update Smart Dashboard UI
        self._update_dashboard_ui(laptop_info, phone_info, estimate)

        # 5. Feed Realtime Power Flow Chart
        phone_w = estimate.phone_power_w or (phone_info.charging_power_w if phone_info.charging_power_w else None)
        laptop_w = laptop_info.discharge_rate_w
        self.power_chart.add_sample(phone_w, laptop_w)

        # 6. Safety Monitor Checks
        alerts = self.safety_monitor.check_safety(
            laptop_pct=laptop_info.percent,
            is_laptop_plugged=laptop_info.is_plugged,
            phone_connected=phone_info.is_connected,
            phone_temp_c=phone_info.battery_temp_c,
            phone_pct=phone_info.battery_percent
        )
        if alerts:
            latest_alert = alerts[0]
            self.alert_banner.show_alert(latest_alert)
            self._log_event(f"SAFETY ALERT: [{latest_alert.level.value}] {latest_alert.title} - {latest_alert.action_required}")

        # 7. Update AI Advisor Report
        self._update_ai_report(laptop_info, phone_info, estimate)

    def _update_dashboard_ui(
        self,
        laptop_info: LaptopBatteryInfo,
        phone_info: PhoneConnectionInfo,
        estimate: ChargingEstimate
    ):
        # Update Phone Connection Card
        self.device_name_label.setText(phone_info.device_name)

        if phone_info.is_connected:
            if phone_info.connection_mode.startswith("ADB"):
                self.conn_badge.setText("ADB CONNECTED")
                self.conn_badge.setStyleSheet(f"background: #064E3B; color: {COLOR_ACCENT_GREEN}; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 8px;")
            elif "Apple" in phone_info.connection_mode:
                self.conn_badge.setText("APPLE DEVICE (PnP)")
                self.conn_badge.setStyleSheet(f"background: #1E3A8A; color: {COLOR_ACCENT_BLUE}; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 8px;")
            else:
                self.conn_badge.setText("PnP / MTP CONNECTED")
                self.conn_badge.setStyleSheet(f"background: #78350F; color: {COLOR_ACCENT_AMBER}; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 8px;")
        else:
            self.conn_badge.setText("DISCONNECTED")
            self.conn_badge.setStyleSheet("background: #1E293B; color: #64748B; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 8px;")

        # Update Gauge
        is_restricted = (phone_info.is_connected and phone_info.battery_percent is None)
        status_text = phone_info.battery_status or ("RESTRICTED" if is_restricted else "NO DEVICE")
        subtext = phone_info.telemetry_source if phone_info.is_connected else "Connect via USB cable"

        self.phone_gauge.update_state(
            percent=phone_info.battery_percent,
            is_charging=phone_info.is_connected and (phone_info.battery_status == "Charging" or is_restricted),
            is_restricted=is_restricted,
            status_text=status_text,
            subtext=subtext
        )

        # Update Notice
        if phone_info.telemetry_limitations_reason:
            self.telemetry_notice_label.setText(phone_info.telemetry_limitations_reason)
        else:
            self.telemetry_notice_label.setText("Streaming authentic hardware battery telemetry via Android BatteryService.")

        # Update 6 Metric Cards
        # 1. Power
        if estimate.phone_power_w is not None:
            self.card_power.set_value(f"{estimate.phone_power_w:.2f} W", "Measured Inflow", True, COLOR_ACCENT_BLUE)
        elif phone_info.is_connected:
            spec = USB_SPECS.get(self.selected_port_spec, USB_SPECS["USB_3_0"])
            self.card_power.set_value(f"{spec.power_watts:.1f} W Max", "Port Spec Bound", True)
        else:
            self.card_power.set_value("Unavailable", "Disconnected", False)

        # 2. Voltage
        if phone_info.battery_voltage_v is not None:
            self.card_voltage.set_value(f"{phone_info.battery_voltage_v:.3f} V", "Cell / VBUS Voltage", True)
        elif phone_info.is_connected:
            self.card_voltage.set_value("5.00 V Nom", "Standard USB VBUS", True)
        else:
            self.card_voltage.set_value("Unavailable", "Disconnected", False)

        # 3. Current
        if phone_info.charging_current_ma is not None:
            self.card_current.set_value(f"{phone_info.charging_current_ma:.0f} mA", "Measured Current", True)
        elif phone_info.is_connected:
            spec = USB_SPECS.get(self.selected_port_spec, USB_SPECS["USB_3_0"])
            self.card_current.set_value(f"{spec.current * 1000:.0f} mA Max", "Port Current Ceiling", True)
        else:
            self.card_current.set_value("Unavailable", "Disconnected", False)

        # 4. Temperature
        if phone_info.battery_temp_c is not None:
            temp = phone_info.battery_temp_c
            color = COLOR_ACCENT_RED if temp >= 42 else (COLOR_ACCENT_AMBER if temp >= 38 else COLOR_ACCENT_GREEN)
            self.card_temp.set_value(f"{temp:.1f} °C", "Normal" if temp < 38 else "Elevated", True, color)
        else:
            self.card_temp.set_value("Unavailable", "OS Restricted (MTP)", False)

        # 5. Estimated Time
        if estimate.time_to_80_mins is not None:
            hrs = estimate.time_to_80_mins // 60
            mins = estimate.time_to_80_mins % 60
            time_str = f"{hrs}h {mins}m to 80%" if hrs > 0 else f"{mins}m to 80%"
            self.card_time.set_value(time_str, f"+{estimate.charge_rate_pct_per_hour:.0f}%/hr CC phase", True)
        elif phone_info.is_connected and estimate.charge_rate_pct_per_hour:
            self.card_time.set_value(f"~{estimate.charge_rate_pct_per_hour:.0f}% / hr", "Estimated Rate (Port Bound)", True)
        else:
            self.card_time.set_value("Unavailable", "No battery data", False)

        # 6. Transfer Efficiency
        if estimate.transfer_efficiency_pct is not None:
            color = COLOR_ACCENT_GREEN if estimate.transfer_efficiency_pct >= 40 else COLOR_ACCENT_AMBER
            self.card_eff.set_value(f"{estimate.transfer_efficiency_pct:.1f} %", "Laptop-to-Phone Ratio", True, color)
        elif laptop_info.is_plugged:
            self.card_eff.set_value("Mains Power", "AC Adapter Energized", True)
        else:
            self.card_eff.set_value("-- %", "Awaiting discharge data", False)

        # Host Controller Info
        ctrl_name = phone_info.detected_usb_controller or "Intel/AMD xHCI USB Controller"
        self.hw_info_label.setText(f"Active Host Controller: {ctrl_name}")

    def _update_ai_report(
        self,
        laptop_info: LaptopBatteryInfo,
        phone_info: PhoneConnectionInfo,
        estimate: ChargingEstimate
    ):
        report = self.ai_advisor.analyze(laptop_info, phone_info, estimate, self.is_emergency_mode)
        self.last_ai_report = report

        self.ai_summary_label.setText(report.summary)
        if report.bottlenecks:
            self.ai_bottlenecks_label.setText("Bottlenecks Detected:\n" + "\n".join([f"• {b}" for b in report.bottlenecks]))
        else:
            self.ai_bottlenecks_label.setText("No critical charging bottlenecks detected.")

        # Rebuild action items
        # Clear previous widgets
        while self.actions_vbox.count():
            item = self.actions_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for act in report.actions:
            card = QFrame()
            card.setStyleSheet(f"background: #162032; border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 10px;")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 8, 10, 8)
            c_layout.setSpacing(4)

            top_row = QHBoxLayout()
            c_cat = QLabel(f"[{act.category.upper()}] {act.title}")
            c_cat.setStyleSheet("color: #F8FAFC; font-weight: 700; font-size: 12px;")
            top_row.addWidget(c_cat)
            top_row.addStretch()

            impact_badge = QLabel(act.impact)
            impact_badge.setStyleSheet(f"background: #0C4A6E; color: {COLOR_ACCENT_BLUE}; font-weight: 700; font-size: 10px; border-radius: 4px; padding: 2px 6px;")
            top_row.addWidget(impact_badge)
            c_layout.addLayout(top_row)

            detail_lbl = QLabel(act.detail)
            detail_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
            detail_lbl.setWordWrap(True)
            c_layout.addWidget(detail_lbl)

            self.actions_vbox.addWidget(card)

        self.actions_vbox.addStretch()

    # -------------------------------------------------------------
    # User Interactions & Handlers
    # -------------------------------------------------------------
    def _toggle_demo_mode(self):
        self.is_demo_mode = not self.is_demo_mode
        if self.is_demo_mode:
            self.demo_toggle_btn.setText("🎮 Demo Mode: ACTIVE")
            self.demo_toggle_btn.setStyleSheet(f"background: #B45309; color: #FFFFFF; border: 1px solid #F59E0B; font-weight: 700;")
            self.demo_banner.show()
            self._log_event("DEMO MODE ACTIVATED: Synthesizing realistic hardware telemetry profiles.")
        else:
            self.demo_toggle_btn.setText("🎮 Demo Mode: OFF")
            self.demo_toggle_btn.setStyleSheet("")
            self.demo_banner.hide()
            self._log_event("DEMO MODE DEACTIVATED: Switched back to physical hardware scanning.")

        self._poll_telemetry()

    def _on_sim_scenario_changed(self, scenario_id: str):
        self.simulator.set_scenario(scenario_id)
        self._log_event(f"Demo scenario switched to: {scenario_id}")
        self._poll_telemetry()

    def _toggle_emergency_mode(self):
        self.is_emergency_mode = not self.is_emergency_mode
        if self.is_emergency_mode:
            self.emergency_btn.setText("⚡ DISENGAGE EMERGENCY CHARGE MODE")
            self.emergency_btn.setObjectName("EmergencyButtonActive")
            self.emergency_btn.setStyle(self.emergency_btn.style())
            self.emergency_banner.show()
            self.chk_keep_awake.setChecked(True)

            # Win32 Execution State Lock
            self.power_manager.enable_emergency_keep_awake(allow_display_sleep=True)
            self.emergency_status_desc.setText(
                "Active: Laptop execution locked awake. Away Mode armed. USB ports will remain powered with lid closed."
            )
            self._log_event("EMERGENCY CHARGE MODE ENGAGED: Win32 SetThreadExecutionState lock active.")
        else:
            self.emergency_btn.setText("⚡ ENGAGE EMERGENCY CHARGE MODE")
            self.emergency_btn.setObjectName("EmergencyButtonInactive")
            self.emergency_btn.setStyle(self.emergency_btn.style())
            self.emergency_banner.hide()
            self.chk_keep_awake.setChecked(False)

            self.power_manager.disable_emergency_keep_awake()
            self.emergency_status_desc.setText("Status: Standby. Standard Windows power policies active.")
            self._log_event("EMERGENCY CHARGE MODE DISENGAGED: Standard power management restored.")

    def _on_reserve_slider_changed(self, val: int):
        self.reserve_label.setText(f"{val}%")
        self.safety_monitor.laptop_reserve_pct = float(val)

    def _on_port_spec_changed(self, index: int):
        self.selected_port_spec = self.port_select_combo.currentData()
        self._poll_telemetry()

    def _open_physics_dialog(self):
        dlg = PhysicsReportDialog(self)
        dlg.exec()

    def _ask_assistant(self, query: str):
        if not hasattr(self, "last_ai_report"):
            return
        answer = self.ai_advisor.ask(query, self.last_ai_report)
        self.chat_browser.setMarkdown(answer)

    def _on_submit_custom_query(self):
        text = self.prompt_input.text().strip()
        if not text:
            return
        self.prompt_input.clear()
        self._ask_assistant(text)

    def _on_api_key_changed(self, text: str):
        key = text.strip()
        self.ai_advisor.update_api_key(key)
        if key:
            self.llm_status_badge.setText("Gemini LLM Active")
            self.llm_status_badge.setStyleSheet(f"color: {COLOR_ACCENT_BLUE}; font-size: 10px; font-weight: 600; background: #0C4A6E; padding: 2px 6px; border-radius: 4px;")
        else:
            self.llm_status_badge.setText("100% Offline Expert System")
            self.llm_status_badge.setStyleSheet(f"color: {COLOR_ACCENT_GREEN}; font-size: 10px; font-weight: 600; background: #0D261E; padding: 2px 6px; border-radius: 4px;")

    def _log_event(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_browser.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        # Always restore Windows execution state on app close
        if self.is_emergency_mode:
            self.power_manager.disable_emergency_keep_awake()
        event.accept()
