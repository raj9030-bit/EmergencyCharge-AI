"""
Custom Circular and Linear Battery Gauges.
Renders high-DPI anti-aliased vector arcs, status badges, and charge indicators.
Honors unavailable data by rendering honest dashed restricted states instead of mock values.
"""

import math
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QWidget

from emergencycharge.ui.styles import (
    COLOR_ACCENT_AMBER,
    COLOR_ACCENT_BLUE,
    COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GREEN,
    COLOR_ACCENT_RED,
    COLOR_BORDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class CircularBatteryGauge(QWidget):
    """Large circular radial battery gauge with charging glow and honest restricted states."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)

        self._percent: Optional[float] = None
        self._is_charging: bool = False
        self._is_restricted: bool = False
        self._status_text: str = "NO DEVICE"
        self._subtext: str = "Connect via USB"

        self._pulse_angle: float = 0.0

        # Animation timer for charging pulse
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_tick)
        self._anim_timer.start(50)  # 20 FPS smooth animation

    def _on_tick(self):
        if self._is_charging:
            self._pulse_angle = (self._pulse_angle + 3.0) % 360.0
            self.update()

    def update_state(
        self,
        percent: Optional[float],
        is_charging: bool = False,
        is_restricted: bool = False,
        status_text: str = "",
        subtext: str = ""
    ):
        self._percent = percent
        self._is_charging = is_charging
        self._is_restricted = is_restricted
        self._status_text = status_text
        self._subtext = subtext
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)
        center = QPointF(width / 2.0, height / 2.0)
        radius = (side / 2.0) - 18.0

        rect = QRectF(center.x() - radius, center.y() - radius, radius * 2.0, radius * 2.0)
        pen_width = 14.0

        # 1. Background Track
        track_pen = QPen(QColor(COLOR_BORDER), pen_width)
        track_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, int(225 * 16), int(-270 * 16))

        # 2. Value Arc
        if self._percent is not None:
            pct = max(0.0, min(100.0, self._percent))
            span_angle = - (pct / 100.0) * 270.0

            # Determine color
            if pct <= 20.0:
                color_start = QColor(COLOR_ACCENT_RED)
                color_end = QColor(COLOR_ACCENT_AMBER)
            elif pct <= 45.0:
                color_start = QColor(COLOR_ACCENT_AMBER)
                color_end = QColor(COLOR_ACCENT_CYAN)
            else:
                color_start = QColor(COLOR_ACCENT_BLUE)
                color_end = QColor(COLOR_ACCENT_GREEN)

            # Draw gradient arc
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0.0, color_start)
            grad.setColorAt(1.0, color_end)

            arc_pen = QPen(QBrush(grad), pen_width)
            arc_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(arc_pen)
            painter.drawArc(rect, int(225 * 16), int(span_angle * 16))

            # Charging animated accent pip
            if self._is_charging:
                glow_pen = QPen(QColor("#FFFFFF"), pen_width + 2)
                glow_pen.setCapStyle(Qt.RoundCap)
                glow_rad = math.radians(225 + span_angle)
                pip_x = center.x() + radius * math.cos(glow_rad)
                pip_y = center.y() - radius * math.sin(glow_rad)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#FFFFFF"))
                painter.drawEllipse(QPointF(pip_x, pip_y), 4.0, 4.0)

        elif self._is_restricted:
            # Render dashed arc for Restricted/MTP state
            dash_pen = QPen(QColor(COLOR_ACCENT_AMBER), pen_width / 2.0)
            dash_pen.setStyle(Qt.DashLine)
            dash_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(dash_pen)
            painter.drawArc(rect, int(225 * 16), int(-270 * 16))

        # 3. Inner Center Text
        # Percentage Value
        painter.setPen(QColor(COLOR_TEXT_PRIMARY))
        font_pct = QFont("Segoe UI", int(side * 0.16), QFont.Bold)
        painter.setFont(font_pct)

        if self._percent is not None:
            pct_str = f"{self._percent:.1f}%"
        elif self._is_restricted:
            pct_str = "MTP"
        else:
            pct_str = "--"

        pct_rect = QRectF(center.x() - radius, center.y() - (side * 0.22), radius * 2.0, side * 0.28)
        painter.drawText(pct_rect, Qt.AlignCenter, pct_str)

        # Status text
        painter.setPen(QColor(COLOR_ACCENT_BLUE if self._is_charging else COLOR_TEXT_SECONDARY))
        font_status = QFont("Segoe UI", int(side * 0.065), QFont.DemiBold)
        painter.setFont(font_status)
        status_rect = QRectF(center.x() - radius, center.y() + (side * 0.05), radius * 2.0, side * 0.14)
        painter.drawText(status_rect, Qt.AlignCenter, self._status_text)

        # Subtext / detail
        painter.setPen(QColor(COLOR_TEXT_MUTED))
        font_sub = QFont("Segoe UI", int(side * 0.052))
        painter.setFont(font_sub)
        sub_rect = QRectF(center.x() - radius, center.y() + (side * 0.18), radius * 2.0, side * 0.14)
        painter.drawText(sub_rect, Qt.AlignCenter, self._subtext)


class HorizontalBatteryBar(QWidget):
    """Linear compact battery bar with icon and color grading."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(14)
        self.setMinimumWidth(100)
        self._percent: float = 100.0
        self._is_plugged: bool = False

    def update_state(self, percent: float, is_plugged: bool):
        self._percent = max(0.0, min(100.0, percent))
        self._is_plugged = is_plugged
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        radius = 4.0

        # Background track
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(COLOR_BORDER))
        painter.drawRoundedRect(rect, radius, radius)

        # Filled portion
        fill_width = (self._percent / 100.0) * rect.width()
        if fill_width > 2.0:
            fill_rect = QRectF(rect.x(), rect.y(), fill_width, rect.height())

            if self._percent <= 20.0:
                color = QColor(COLOR_ACCENT_RED)
            elif self._percent <= 40.0:
                color = QColor(COLOR_ACCENT_AMBER)
            else:
                color = QColor(COLOR_ACCENT_GREEN if self._is_plugged else COLOR_ACCENT_BLUE)

            painter.setBrush(color)
            painter.drawRoundedRect(fill_rect, radius, radius)
