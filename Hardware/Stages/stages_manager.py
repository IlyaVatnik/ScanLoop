# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 16:37:13 2026

@author: Александр
"""
# Hardware/Stages/stages_manager.py
__date__ = '2026.05.11'
__version__ = '2.5.0'

import logging
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

try:
    from Hardware.Stages.Standa.standa_stages import StandaAxis
except ImportError as e:
    logger.warning(f"Не удалось загрузить модуль Standa: {e}")
    StandaAxis = None

try:
    from Hardware.Stages.LBTEK.lbtek_stages import LBTEKAxis
except ImportError as e:
    logger.warning(f"Не удалось загрузить модуль LBTEK: {e}")
    LBTEKAxis = None

try:
    from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsCube, ThorlabsBSM
except (ImportError, FileNotFoundError) as e:
    logger.warning(f"Не удалось загрузить модуль Thorlabs: {e}")
    ThorlabsCube = ThorlabsBSM = None


class Stages(QObject):
    connected = pyqtSignal()
    stopped = pyqtSignal()
    S_print_error = pyqtSignal(str)

    def __init__(self, config=None):
        super().__init__()
        self.axes = {'X': None, 'Y': None, 'Z': None}
        # Координаты в физических шагах энкодера (long int без округления)
        self.abs_position_steps = {'X': 0, 'Y': 0, 'Z': 0}
        self.relative_position_steps = {'X': 0, 'Y': 0, 'Z': 0}
        self.zero_position_steps = {'X': 0, 'Y': 0, 'Z': 0}

        # Координаты в микронах с максимальной точностью float
        self.abs_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.relative_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.zero_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self._is_moving = False

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(300)
        self._poll_timer.timeout.connect(self._on_poll_timer)

        if config:
            self.setup_stages(config)

    def _on_poll_timer(self):
        """Опрос реального положения столиков при простое (отслеживание ручного вращения крутилок)"""
        if self._is_moving:
            return
        changed = False
        for key, axis_obj in self.axes.items():
            if axis_obj is not None:
                try:
                    if hasattr(axis_obj, 'get_position_steps'):
                        steps = int(axis_obj.get_position_steps())
                        if steps != self.abs_position_steps[key]:
                            self.abs_position_steps[key] = steps
                            self.abs_position[key] = float(axis_obj.get_position())
                            changed = True
                    else:
                        pos = float(axis_obj.get_position())
                        if abs(self.abs_position[key] - pos) >= 0.0001:
                            self.abs_position[key] = pos
                            min_step = self.get_min_step(key)
                            self.abs_position_steps[key] = int(round(pos / min_step)) if min_step else 0
                            changed = True
                except Exception:
                    pass
        if changed:
            self.update_relative_positions()
            self.stopped.emit()

    def get_min_step(self, key: str) -> float:
        """Возвращает минимальный шаг подвижки по заданной оси (мкм)."""
        axis_obj = self.axes.get(key)
        if axis_obj and hasattr(axis_obj, 'get_min_step'):
            return float(axis_obj.get_min_step())
        if axis_obj and hasattr(axis_obj, 'encoder_step'):
            return float(axis_obj.encoder_step)
        return 0.028939403847844007  # Заводской шаг сервопривода Thorlabs Z8

    def set_stage_velocity(self, key: str, max_velocity_mm_s: float, acceleration_mm_s2: float):
        """Динамическая установка скорости и разгона для оси."""
        axis_obj = self.axes.get(key)
        if axis_obj and hasattr(axis_obj, 'set_velocity'):
            axis_obj.set_velocity(max_velocity_mm_s, acceleration_mm_s2)

    def setup_stages(self, config):
        driver_map = {
            'STANDA': StandaAxis,
            'LBTEK': LBTEKAxis,
        }

        for axis_key, params in config.items():
            if params is None:
                continue
            try:
                stage_type = params['type'].upper()
                serial = params.get('serial', params.get('port', ''))

                if stage_type == 'THORLABS':
                    raw = serial
                    if not raw:
                        continue
                    vel = params.get('velocity', 2.0)
                    acc = params.get('acceleration', 1.5)

                    if 'B' in raw and raw[0].isdigit():
                        channel = int(raw[0])
                        serial = raw[2:]
                        if ThorlabsBSM:
                            self.axes[axis_key] = ThorlabsBSM(serial, channel, vel, acc)
                        else:
                            continue
                    elif raw.startswith('B'):
                        serial = raw[1:]
                        if ThorlabsBSM:
                            self.axes[axis_key] = ThorlabsBSM(serial, 0, vel, acc)
                        else:
                            continue
                    elif raw.startswith('K'):
                        serial = raw[1:]
                        if ThorlabsCube:
                            self.axes[axis_key] = ThorlabsCube(serial, max_velocity_mm_s=vel, acceleration_mm_s2=acc)
                        else:
                            continue
                    else:
                        if ThorlabsCube:
                            self.axes[axis_key] = ThorlabsCube(raw, max_velocity_mm_s=vel, acceleration_mm_s2=acc)
                        else:
                            continue
                else:
                    driver_class = driver_map.get(stage_type)
                    if driver_class is None:
                        self.S_print_error.emit(f"Неизвестный тип подвижки: {stage_type}")
                        continue
                    port = params.get('port', '')
                    self.axes[axis_key] = driver_class(port)

                logger.info(f"Ось {axis_key} ({stage_type} на {serial}) успешно инициализирована.")

            except Exception as e:
                logger.error(f"Ошибка инициализации оси {axis_key}:\n{traceback.format_exc()}")
                self.S_print_error.emit(f"Ошибка инициализации оси {axis_key}: {e}")

        self.update_all_absolute_positions()

        if any(ax is not None for ax in self.axes.values()):
            self._poll_timer.start()
            self.connected.emit()

    def shiftOnArbitrary(self, key: str, distance: float):
        logger.info(f"[Stages.shiftOnArbitrary] key={key}, distance={distance}")
        axis_obj = self.axes.get(key)

        if axis_obj is None:
            self.S_print_error.emit(f"Ось {key} не подключена.")
            return

        self._is_moving = True
        try:
            axis_obj.move_relative(float(distance))
            if hasattr(axis_obj, 'wait_for_stop'):
                axis_obj.wait_for_stop()
            logger.info(f"[Stages.shiftOnArbitrary] move_relative завершён")
            
            if hasattr(axis_obj, 'get_position_steps'):
                self.abs_position_steps[key] = int(axis_obj.get_position_steps())
            else:
                min_step = self.get_min_step(key)
                self.abs_position_steps[key] = int(round(float(axis_obj.get_position()) / min_step)) if min_step else 0

            self.abs_position[key] = float(axis_obj.get_position())
            self.update_relative_positions()
            self.stopped.emit()
            logger.info(f"[Stages.shiftOnArbitrary] stopped.emit() отправлен, pos={self.abs_position[key]:.5f} мкм ({self.abs_position_steps[key]} шагов)")

        except Exception as e:
            logger.error(f"[Stages.shiftOnArbitrary] ИСКЛЮЧЕНИЕ:\n{traceback.format_exc()}")
            self.S_print_error.emit(f"Ошибка при движении оси {key}: {e}")
        finally:
            self._is_moving = False

    def move_home(self, key: str):
        axis_obj = self.axes.get(key)
        if axis_obj is None:
            return
        self._is_moving = True
        try:
            axis_obj.move_home()
            if hasattr(axis_obj, 'wait_for_stop'):
                axis_obj.wait_for_stop()
            self.update_all_absolute_positions()
            self.stopped.emit()
        except Exception as e:
            logger.error(f"[Stages.move_home] ИСКЛЮЧЕНИЕ:\n{traceback.format_exc()}")
            self.S_print_error.emit(f"Ошибка move_home оси {key}: {e}")
        finally:
            self._is_moving = False

    def set_zero_positions(self, zeros_list):
        for i, key in enumerate(['X', 'Y', 'Z']):
            if i < len(zeros_list):
                val = float(zeros_list[i])
                self.zero_position[key] = val
                min_step = self.get_min_step(key)
                self.zero_position_steps[key] = int(round(val / min_step)) if min_step else 0
        self.update_relative_positions()

    def update_relative_positions(self):
        for key in ['X', 'Y', 'Z']:
            self.relative_position_steps[key] = int(self.abs_position_steps[key] - self.zero_position_steps[key])
            self.relative_position[key] = float(self.abs_position[key] - self.zero_position[key])

    def update_all_absolute_positions(self):
        for key, axis_obj in self.axes.items():
            if axis_obj is not None:
                try:
                    if hasattr(axis_obj, 'get_position_steps'):
                        self.abs_position_steps[key] = int(axis_obj.get_position_steps())
                    else:
                        min_step = self.get_min_step(key)
                        self.abs_position_steps[key] = int(round(float(axis_obj.get_position()) / min_step)) if min_step else 0
                    self.abs_position[key] = float(axis_obj.get_position())
                    logger.debug(f"[Stages] update_position axis={key}: {self.abs_position[key]:.5f} um ({self.abs_position_steps[key]} steps)")
                except Exception as e:
                    logger.error(f"Не удалось прочитать позицию оси {key}: {traceback.format_exc()}")
                    self.abs_position[key] = 0.0
                    self.abs_position_steps[key] = 0
        self.update_relative_positions()
        logger.debug(f"[Stages] abs_positions: {self.abs_position}")

    def close_all(self):
        try:
            if hasattr(self, '_poll_timer') and self._poll_timer is not None:
                self._poll_timer.stop()
        except (RuntimeError, TypeError):
            pass
        for key, axis_obj in self.axes.items():
            if axis_obj is not None:
                try:
                    axis_obj.close()
                except Exception as e:
                    logger.error(f"Ошибка закрытия оси {key}: {e}")

    def __del__(self):
        try:
            self.close_all()
        except Exception:
            pass