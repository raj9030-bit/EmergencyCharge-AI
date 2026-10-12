"""
EmergencyCharge AI — Application Entry Point.
"""

import logging
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from emergencycharge.config import APP_TITLE, VERSION
from emergencycharge.ui.main_window import MainWindow


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    setup_logging()
    logger = logging.getLogger("emergencycharge")
    logger.info(f"Starting {APP_TITLE} v{VERSION}...")

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("DeepMind Advanced Systems")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
