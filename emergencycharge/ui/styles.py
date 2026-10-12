"""
Design System, Color Palette, and Qt StyleSheets for EmergencyCharge AI.
Dark interface with subtle electric-blue (#00D2FF) accents and modern engineering cards.
"""

# Palette
COLOR_BG_DARK = "#090D16"
COLOR_BG_CARD = "#111827"
COLOR_BG_CARD_ALT = "#162032"
COLOR_BORDER = "#1E293B"
COLOR_BORDER_ACCENT = "#1E3A8A"

COLOR_ACCENT_BLUE = "#00D2FF"
COLOR_ACCENT_BLUE_HOVER = "#38BDF8"
COLOR_ACCENT_CYAN = "#06B6D4"
COLOR_ACCENT_GREEN = "#10B981"
COLOR_ACCENT_AMBER = "#F59E0B"
COLOR_ACCENT_RED = "#EF4444"

COLOR_TEXT_PRIMARY = "#F8FAFC"
COLOR_TEXT_SECONDARY = "#94A3B8"
COLOR_TEXT_MUTED = "#64748B"

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #090D16;
}

QWidget {
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", sans-serif;
    color: #F8FAFC;
    font-size: 13px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0D131F;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #1E293B;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #00D2FF;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #1E293B;
    background: #090D16;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #0F172A;
    color: #94A3B8;
    padding: 10px 22px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #1E293B;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #111827;
    color: #00D2FF;
    border-top: 2px solid #00D2FF;
    border-bottom: 1px solid #111827;
}
QTabBar::tab:hover:!selected {
    background: #1E293B;
    color: #F8FAFC;
}

/* Cards */
QFrame.CardFrame {
    background-color: #111827;
    border: 1px solid #1E293B;
    border-radius: 10px;
}

QFrame.CardFrameHighlighted {
    background-color: #162032;
    border: 1px solid #00D2FF;
    border-radius: 10px;
}

/* Buttons */
QPushButton {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #334155;
    border-color: #00D2FF;
    color: #00D2FF;
}
QPushButton:pressed {
    background-color: #0F172A;
}
QPushButton:disabled {
    background-color: #0F172A;
    color: #475569;
    border-color: #1E293B;
}

/* Emergency Mode Giant Button */
QPushButton#EmergencyButtonInactive {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:1 #0284C7);
    color: #FFFFFF;
    border: 1px solid #38BDF8;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 700;
    padding: 12px 24px;
}
QPushButton#EmergencyButtonInactive:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #0EA5E9);
    border: 1px solid #00D2FF;
}

QPushButton#EmergencyButtonActive {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
    color: #FFFFFF;
    border: 2px solid #34D399;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 700;
    padding: 12px 24px;
}
QPushButton#EmergencyButtonActive:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0D131F;
    border: 1px solid #1E293B;
    border-radius: 6px;
    color: #F8FAFC;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #00D2FF;
    selection-color: #090D16;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #00D2FF;
}

/* ComboBox */
QComboBox {
    background-color: #0D131F;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 6px 12px;
    color: #F8FAFC;
    font-weight: 500;
}
QComboBox:hover {
    border-color: #00D2FF;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #111827;
    border: 1px solid #1E293B;
    color: #F8FAFC;
    selection-background-color: #1E293B;
    selection-color: #00D2FF;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #1E293B;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #00D2FF;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #F8FAFC;
    border: 2px solid #00D2FF;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #00D2FF;
}

/* Tooltips */
QToolTip {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    padding: 6px;
    border-radius: 4px;
}
"""
