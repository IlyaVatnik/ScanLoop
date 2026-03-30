# -*- coding: utf-8 -*-
import os
import sys

# --- ВАЖНЫЙ ФИКС ДЛЯ КОМПИЛЯЦИИ ---
# Заставляем Matplotlib использовать правильный оконный движок PyQt5
import matplotlib
matplotlib.use('Qt5Agg')
# ----------------------------------

from PyQt5 import QtWidgets
from Windows_GUI.MainWindow import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())