# -*- coding: utf-8 -*-
import os
import sys
from PyQt5 import uic

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(current_dir, "MainWindow.ui")
py_file = os.path.join(current_dir, "MainWindowUI.py")

with open(py_file, "w", encoding="utf-8") as fout:
    uic.compileUi(ui_file, fout)

print("MainWindow.ui successfully converted to MainWindowUI.py")