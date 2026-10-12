"""
Real-Time Power Transfer and Discharge Chart.
Custom QPainter vector strip-chart plotting phone charging wattage
vs laptop discharge rate over a rolling time window.
"""

from collections import deque
from typing import Deque, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from emergencycharge.ui.styles import (
    COLOR_ACCENT_AMBER,
    COLOR_ACCENT_BLUE,
    COLOR_ACCENT_CYAN,
    COLOR_BORDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class RealtimePowerChart(QWidget):
    """Visualizes live laptop-to-phone power flow and system discharge rate."""

    def __init__(self, max_points: int = 50, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.max_points = max_points

        # Data series (rolling window)
        self.phone_watts: Deque[float] = deque([0.0] * max_points, maxlen=max_points)
        self.laptop_watts: Deque[float] = deque([0.0] * max_points, maxlen=max_points)

    def add_sample(self, phone_w: Optional[float], laptop_w: Optional[float]):
        pw = float(phone_w) if phone_w is not None and phone_w >= 0 else 0.0
        lw = float(laptop_w) if laptop_w is not None and laptop_w >= 0 else 0.0
        self.phone_watts.append(pw)
        self.laptop_watts.append(lw)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        padding_left = 42.0
        padding_right = 16.0
        padding_top = 28.0
        padding_bottom = 26.0

        chart_w = w - padding_left - padding_right
        chart_h = h - padding_top - padding_bottom

        if chart_w <= 10 or chart_h <= 10:
            return

        # Calculate dynamic max power ceiling
        max_val = max(max(self.phone_watts), max(self.laptop_watts), 10.0)
        max_y = (math_ceil := int((max_val + 4.9) // 5) * 5)

        # 1. Background grid
        painter.setPen(QPen(QColor(COLOR_BORDER), 1, Qt.DotLine))
        font_axis = QFont("Segoe UI", 9)
        painter.setFont(font_axis)

        grid_steps = 4
        for i in range(grid_steps + 1):
            val = (max_y / grid_steps) * i
            y_pos = padding_top + chart_h - (i * (chart_h / grid_steps))

            # Horizontal line
            painter.setPen(QPen(QColor(COLOR_BORDER), 1, Qt.DotLine))
            painter.drawLine(QPointF(padding_left, y_pos), QPointF(w - padding_right, y_pos))

            # Y Axis Label
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            painter.drawText(
                QRectF(0, y_pos - 8, padding_left - 8, 16),
                Qt.AlignRight | Qt.AlignVCenter,
                f"{val:.0f}W"
            )

        # X Axis timeline labels
        painter.setPen(QColor(COLOR_TEXT_MUTED))
        painter.drawText(QRectF(padding_left, h - padding_bottom + 6, 60, 16), Qt.AlignLeft, "-60s")
        painter.drawText(QRectF(w / 2.0 - 30, h - padding_bottom + 6, 60, 16), Qt.AlignCenter, "-30s")
        painter.drawText(QRectF(w - padding_right - 40, h - padding_bottom + 6, 40, 16), Qt.AlignRight, "Now")

        # 2. Draw Legend at Top
        legend_y = 12.0
        # Phone Power Legend
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(COLOR_ACCENT_BLUE))
        painter.drawRoundedRect(QRectF(padding_left, legend_y, 10, 10), 2, 2)
        painter.setPen(QColor(COLOR_TEXT_SECONDARY))
        painter.drawText(QRectF(padding_left + 16, legend_y - 2, 140, 16), Qt.AlignLeft, "Phone Inflow (W)")

        # Laptop Discharge Legend
        laptop_leg_x = padding_left + 160
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(COLOR_ACCENT_AMBER))
        painter.drawRoundedRect(QRectF(laptop_leg_x, legend_y, 10, 10), 2, 2)
        painter.setPen(QColor(COLOR_TEXT_SECONDARY))
        painter.drawText(QRectF(laptop_leg_x + 16, legend_y - 2, 160, 16), Qt.AlignLeft, "Laptop Discharge (W)")

        # Helper to convert index and watts to canvas coords
        def get_coords(idx: int, watts: float) -> QPointF:
            x = padding_left + (idx / (self.max_points - 1)) * chart_w
            y = padding_top + chart_h - (min(watts, max_y) / max_y) * chart_h
            return QPointF(x, y)

        # 3. Draw Laptop Discharge Line (Amber)
        laptop_path = QPainterPath()
        laptop_path.moveTo(get_coords(0, self.laptop_watts[0]))
        for i in range(1, len(self.laptop_watts)):
            laptop_path.lineTo(get_coords(i, self.laptop_watts[i]))

        painter.setPen(QPen(QColor(COLOR_ACCENT_AMBER), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(laptop_path)

        # 4. Draw Phone Inflow Line with Subtle Fill (Electric Blue)
        phone_fill_path = QPainterPath()
        first_pt = get_coords(0, self.phone_watts[0])
        phone_fill_path.moveTo(padding_left, padding_top + chart_h)
        phone_fill_path.lineTo(first_pt)

        phone_line_path = QPainterPath()
        phone_line_path.moveTo(first_pt)

        for i in range(1, len(self.phone_watts)):
            pt = get_coords(i, self.phone_watts[i])
            phone_line_path.lineTo(pt)
            phone_fill_path.lineTo(pt)

        last_pt = get_coords(len(self.phone_watts) - 1, self.phone_watts[-1])
        phone_fill_path.lineTo(last_pt.x(), padding_top + chart_h)
        phone_fill_path.closeSubpath()

        # Fill gradient
        grad = QLinearGradient(0, padding_top, 0, padding_top + chart_h)
        grad.setColorAt(0.0, QColor(0, 210, 255, 60))
        grad.setColorAt(1.0, QColor(0, 210, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(grad)
        painter.drawPath(phone_fill_path)

        # Line stroke
        painter.setPen(QPen(QColor(COLOR_ACCENT_BLUE), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(phone_line_path)

        # Current value marker on latest point
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(last_pt, 3.5, 3.5)
