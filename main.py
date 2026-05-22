# -*- coding: utf-8 -*-
import sys
import os
import logging
from datetime import datetime
import matplotlib

# Убеждаемся, что Matplotlib использует нужный бэкенд
matplotlib.use('Qt5Agg')

# Настройка логирования (файл появится рядом с .exe)
if getattr(sys, 'frozen', False):
    # Если запущен как .exe
    app_dir = os.path.dirname(sys.executable)
else:
    # Если запущен как .py
    app_dir = os.path.dirname(os.path.abspath(__file__))

# Переходим в рабочую директорию (чтобы работали относительные пути к config.json и т.д.)
os.chdir(app_dir)

log_file = os.path.join(app_dir, f"scanloop_{datetime.now():%Y%m%d_%H%M%S}.log")

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

def exception_hook(exc_type, exc_value, exc_tb):
    logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
    # Также выведем ошибку в консоль, если она есть
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = exception_hook
logging.info("=== Application Starting ===")

from PyQt5 import QtWidgets
from Windows_GUI.MainWindow import MainWindow

if __name__ == '__main__':
    logging.info("Initializing Application...")
    app = QtWidgets.QApplication(sys.argv)
    
    # Запуск окна
    window = MainWindow()#(version='2.5.0', date='2026.04.08')
    window.show()
    
    logging.info("Event loop started.")
    sys.exit(app.exec_())