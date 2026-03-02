# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 16:37:13 2026

@author: Александр
"""
__data__='2026.03.02'
__version__='2.4'

# stages_manager.py

from PyQt5.QtCore import QObject, pyqtSignal

# Импортируем драйвер для Standa
# Если файл standa_stages.py лежит в другой папке, поправьте импорт (например, from Hardware.Stages.Standa.standa_stages import StandaAxis)
try:
    from standa_stages import StandaAxis
except ImportError:
    print("Warning: Standa stages module not found or pyximc is missing.")
    StandaAxis = None


class Stages(QObject):
    """
    Единый класс для управления подвижками. 
    Импортирует нужные классы осей на основе переданной конфигурации.
    """
    connected = pyqtSignal()
    stopped = pyqtSignal()
    S_print_error = pyqtSignal(str) # Сигнал для вывода ошибок в лог/GUI
    
    def __init__(self, config=None):
        super().__init__()
        
        self.axes = {'X': None, 'Y': None, 'Z': None}
        self.abs_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.relative_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.zero_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}

        if config:
            self.setup_stages(config)

    def setup_stages(self, config):
        """
        Инициализация осей по словарю конфигурации. Пример:
        config = {
            'X': {'type': 'STANDA', 'id': 'Axis 1'},
            'Y': None, # Ось не используется
            'Z': {'type': 'STANDA', 'id': 'Axis 2'}
        }
        """
        for axis_key, params in config.items():
            if params is None:
                continue
                
            try:
                stage_type = params['type'].upper()
                
                if stage_type == 'STANDA':
                    if StandaAxis is None:
                        raise RuntimeError("Standa module is not loaded.")
                    self.axes[axis_key] = StandaAxis(params['id'])
                
                # Задел на будущее (добавление новых типов подвижек):
                # elif stage_type == 'THORLABS':
                #     self.axes[axis_key] = ThorlabsAxis(params['id'])
                # elif stage_type == 'PI':
                #     self.axes[axis_key] = PiAxis(params['id'])
                
                else:
                    self.S_print_error.emit(f"Unknown stage type: {stage_type}")
            except Exception as e:
                self.S_print_error.emit(f"Error initializing axis {axis_key}: {str(e)}")

        self.update_all_absolute_positions()
        self.connected.emit()

    def set_zero_positions(self, zeros_list):
        """Установка нулей (относительной системы координат). l = [x_0, y_0, z_0]"""
        self.zero_position['X'] = zeros_list[0]
        self.zero_position['Y'] = zeros_list[1]
        self.zero_position['Z'] = zeros_list[2]
        self.update_relative_positions()
    
    def update_relative_positions(self):
        """Перерасчет относительных координат для всех осей"""
        for key in ['X', 'Y', 'Z']:
            if self.abs_position[key] is not None and self.zero_position[key] is not None:
                self.relative_position[key] = self.abs_position[key] - self.zero_position[key]

    def update_all_absolute_positions(self):
        """Опрос реального железа для получения актуальных координат"""
        for key, axis_obj in self.axes.items():
            if axis_obj is not None:
                self.abs_position[key] = axis_obj.get_position()
        self.update_relative_positions()

    def shiftOnArbitrary(self, key: str, distance: float):
        """Сдвиг указанной оси на заданное расстояние (в мкм)"""
        axis_obj = self.axes.get(key)
        if axis_obj is None:
            self.S_print_error.emit(f"Axis {key} is not connected or configured.")
            return

        try:
            axis_obj.move_relative(distance)
            axis_obj.wait_for_stop()
            
            # Обновляем координаты после остановки
            self.abs_position[key] = axis_obj.get_position()
            self.update_relative_positions()
            self.stopped.emit()
        except Exception as e:
            self.S_print_error.emit(f"Error moving axis {key}: {str(e)}")

    def move_home(self, key: str):
        """Отправка указанной оси в домашнюю позицию"""
        axis_obj = self.axes.get(key)
        if axis_obj is None:
            self.S_print_error.emit(f"Axis {key} is not connected.")
            return

        try:
            axis_obj.move_home()
            axis_obj.wait_for_stop()
            
            self.abs_position[key] = axis_obj.get_position()
            self.update_relative_positions()
            self.stopped.emit()
        except Exception as e:
            self.S_print_error.emit(f"Error homing axis {key}: {str(e)}")

    def __del__(self):
        """Корректное закрытие всех открытых соединений при удалении объекта"""
        for axis_obj in self.axes.values():
            if axis_obj is not None:
                try:
                    axis_obj.close()
                except:
                    pass


# =====================================================================
# Пример использования
# =====================================================================
if __name__ == "__main__":
    # Настраиваем, какая железка отвечает за какую ось
    stage_config = {
        'X': {'type': 'STANDA', 'id': 'Axis 1'},
        'Y': {'type': 'STANDA', 'id': 'Axis 3'},
        'Z': {'type': 'STANDA', 'id': 'Axis 2'}
    }

    # Инициализируем менеджер с нашей конфигурацией
    stages = Stages(config=stage_config)

    # Задаем нули программных координат
    stages.set_zero_positions([10.0, 0.0, -5.0])

    print("Initial X relative position:", stages.relative_position['X'])

    # Сдвиг по оси X
    d = 5.0
    print(f"Moving X by {d} mkm...")
    # stages.shiftOnArbitrary('X', d)

    # Удаляем объект, порты закроются автоматически
    del stages
'''  
Как теперь добавлять другие подвижки (например, Thorlabs)?
Создаете файл thorlabs_stages.py.
Внутри пишете класс ThorlabsAxis, у которого обязательно должны быть методы: __init__(id), get_position(), move_relative(dist), move_home(), wait_for_stop(), close().
В stages_manager.py импортируете его и в метод setup_stages добавляете elif stage_type == 'THORLABS': self.axes[axis_key] = ThorlabsAxis(params['id']).
Остальная логика расчета координат, ожидания и выдачи Qt-сигналов сработает автоматически без изменений!
'''  
