# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:31:50 2026

@author: Александр
"""
import os
from PyQt5 import uic

# Автоматически получаем полный путь к папке, где лежит этот скрипт
current_dir = os.path.dirname(os.path.abspath(__file__))

# Собираем абсолютные пути к файлам
ui_file = os.path.join(current_dir, "MainWindow.ui")
py_file = os.path.join(current_dir, "MainWindow.py")

print(f"Ищем файл: {ui_file}")

# Конвертируем
with open(py_file, "w", encoding="utf-8") as fout:
    uic.compileUi(ui_file, fout)

print("Ура! Файл успешно сконвертирован!")