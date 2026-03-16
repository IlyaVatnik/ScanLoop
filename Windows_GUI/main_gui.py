# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 15:45:22 2026

@author: Александр
"""

__data__='2026.03.16'
__version__='2.4'
# -*- coding: utf-8 -*-
import sys
import os
from PyQt5 import QtWidgets, uic

# === МАГИЯ ПУТЕЙ ===
# Получаем абсолютный путь к папке, где лежит этот скрипт (Windows_GUI)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Поднимаемся на уровень выше, чтобы получить путь к корню проекта (ScanLoop)
project_root = os.path.dirname(current_dir)

# Добавляем корень проекта в пути поиска Python, чтобы он видел папку Hardware
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ===================

# Теперь импорт сработает корректно
from Hardware.Stages.stages_manager import Stages 

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Собираем путь: текущая папка (Windows_GUI) + папка 'UIs' + файл 'MainWindowUI.ui'
        ui_path = os.path.join(current_dir, 'UIs', 'MainWindowUI.ui')
        uic.loadUi(ui_path, self)
        
        self.stages = None
        
        # Подключаем ВАШУ кнопку к методу инициализации
        self.pushButton_StagesConnect.clicked.connect(self.init_stages)
        
    def log(self, message):
        """Метод для вывода текста в лог (если есть текстовое поле)"""
        if hasattr(self, 'text_log'):
            self.text_log.append(message)
        else:
            print(message)

    def init_stages(self):
        # Настройки идентификаторов Standa (Axis 1, 2, 3)
        standa_ids = {
            'X': 'Axis 1',
            'Y': 'Axis 3',
            'Z': 'Axis 2'
        }
        
        config = {}
        
        # Читаем значения из выпадающих списков
        selected_x = self.combo_X.currentText()
        selected_y = self.combo_Y.currentText()
        selected_z = self.combo_Z.currentText()
        
        # X
        if selected_x == 'STANDA':
            config['X'] = {'type': 'STANDA', 'id': standa_ids['X']}
        else:
            config['X'] = None
            
        # Y
        if selected_y == 'STANDA':
            config['Y'] = {'type': 'STANDA', 'id': standa_ids['Y']}
        else:
            config['Y'] = None
            
        # Z
        if selected_z == 'STANDA':
            config['Z'] = {'type': 'STANDA', 'id': standa_ids['Z']}
        else:
            config['Z'] = None

        self.log(f"Собранная конфигурация:\n{config}")

        try:
            if self.stages is not None:
                del self.stages # Корректно закрываем порты перед новым подключением
            
            self.log("Подключение к оборудованию...")
            self.stages = Stages(config=config)
            
            self.stages.S_print_error.connect(self.log)
            self.stages.connected.connect(lambda: self.log("Подвижки успешно подключены!"))
            
            # Выводим текущие позиции
            for axis in ['X', 'Y', 'Z']:
                if config[axis] is not None:
                    pos = self.stages.abs_position[axis]
                    self.log(f"Ось {axis} инициализирована. Позиция: {pos}")

        except Exception as e:
            self.log(f"Ошибка инициализации: {str(e)}")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())