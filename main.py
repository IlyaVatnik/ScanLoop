# -*- coding: utf-8 -*-
import sys
import os
import logging
import matplotlib

matplotlib.use('Qt5Agg')

from Utils.logging_setup import setup_logging, \
    install_exception_hooks, install_qt_message_handler, SafeQApplication

logger, LOG_DIR = setup_logging()

from PyQt5 import QtWidgets
from Windows_GUI.MainWindow import MainWindow

if __name__ == '__main__':
    logging.info("Initializing Application...")
    app = SafeQApplication(sys.argv)
    install_qt_message_handler()
    install_exception_hooks()

    window = MainWindow()
    window.show()

    logging.info("Event loop started.")
    sys.exit(app.exec_())
